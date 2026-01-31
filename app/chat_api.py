from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import time
import asyncio
from grok_client import GrokClient
from gemini_client import GeminiClient
from knowledge_manager import KnowledgeManager
from rule_engine import RuleEngine
from prompt_builder import PromptBuilder
from security import SecurityValidator
from conversation_manager import conversation_manager
from operational_safety import abuse_detector, observability_metrics, medical_safety
from logger import logger
from config import get_config

router = APIRouter()
config = get_config()
limiter = Limiter(key_func=get_remote_address)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    version: str = config.widget_version
    debug_info: Optional[dict] = None

class KnowledgeExpansionRequest(BaseModel):
    raw_text: str
    source_tag: str
    domain: Optional[str] = "general"

# Initialize components
grok_client = GrokClient()
gemini_client = GeminiClient()
knowledge_manager = KnowledgeManager()
rule_engine = RuleEngine()
prompt_builder = PromptBuilder()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{config.rate_limit_requests}/{config.rate_limit_window}seconds")
async def chat(request: ChatRequest, http_request: Request):
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    client_ip = get_remote_address(http_request)
    user_agent = http_request.headers.get("user-agent", "")
    debug_info = {} if config.debug_mode else None
    
    try:
        # Check for abuse patterns
        if abuse_detector.check_request_abuse(client_ip, user_agent):
            logger.log_security_event("rate_limit_abuse", client_ip, {
                "user_agent": user_agent,
                "session_id": session_id[:8] + "***"
            })
            raise HTTPException(status_code=429, detail="Too many requests")
        
        if abuse_detector.is_ip_blocked(client_ip):
            logger.log_security_event("ip_blocked", client_ip, {"reason": "too_many_errors"})
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Security validation
        sanitized_message = SecurityValidator.sanitize_user_input(request.message)
        
        if not sanitized_message.strip():
            raise HTTPException(status_code=400, detail="Invalid message")
        
        # Check for suspicious message content
        if abuse_detector.check_message_abuse(sanitized_message):
            logger.log_security_event("suspicious_message", client_ip, {
                "message_length": len(sanitized_message),
                "session_id": session_id[:8] + "***"
            })
            return ChatResponse(
                response="I can't process that type of message. Please try a different question.",
                session_id=session_id,
                debug_info=debug_info
            )
        
        # Load rules and knowledge with error handling
        try:
            rules = rule_engine.load_rules()
            relevant_knowledge = knowledge_manager.find_relevant_knowledge(
                sanitized_message, 
                max_results=config.max_knowledge_entries
            )
            
            # Get conversation context
            conversation_context = conversation_manager.get_conversation_context(session_id)
            
            if config.debug_mode:
                debug_info.update({
                    "knowledge_matches": len(relevant_knowledge),
                    "conversation_context_length": len(conversation_context),
                    "sanitized_message": sanitized_message
                })
                
        except Exception as e:
            logger.log_api_error("knowledge_system", e, {"session_id": session_id})
            abuse_detector.log_error(client_ip)
            rules = "Be helpful and accurate."
            relevant_knowledge = []
            conversation_context = ""
        
        # Build prompt with context limits
        prompt = prompt_builder.build_chat_prompt(
            rules=rules,
            knowledge=relevant_knowledge,
            user_message=sanitized_message,
            conversation_context=conversation_context
        )
        
        prompt = SecurityValidator.limit_context_size(prompt)
        
        if config.debug_mode:
            debug_info["prompt_length"] = len(prompt)
            # Only show prompt preview in debug mode, never in production
            if config.debug_mode:
                debug_info["prompt_preview"] = prompt[:200] + "..." if len(prompt) > 200 else prompt
        
        # Get response from Grok with retries
        response, token_usage = await _get_response_with_retry(grok_client, prompt, session_id)
        
        # Check if medical disclaimer is required
        if medical_safety.requires_medical_disclaimer(sanitized_message, relevant_knowledge):
            response = medical_safety.add_medical_disclaimer(response)
        
        # Add to conversation history
        conversation_manager.add_message(session_id, sanitized_message, response)
        
        # Log successful interaction (no sensitive data)
        processing_time = time.time() - start_time
        logger.log_chat(session_id, sanitized_message, response, processing_time, client_ip)
        observability_metrics.record_request(processing_time)
        
        if config.log_token_usage and token_usage:
            logger.chat_logger.info(f"Token usage - Session: {session_id[:8]}***, Tokens: {token_usage}")
        
        if config.debug_mode:
            debug_info.update({
                "processing_time": processing_time,
                "token_usage": token_usage,
                "medical_disclaimer_added": medical_safety.requires_medical_disclaimer(sanitized_message, relevant_knowledge)
            })
        
        return ChatResponse(
            response=response, 
            session_id=session_id,
            debug_info=debug_info if config.debug_mode else None
        )
        
    except HTTPException:
        abuse_detector.log_error(client_ip)
        observability_metrics.record_error("http_exception")
        raise
    except Exception as e:
        logger.log_api_error("chat_endpoint", e, {"session_id": session_id})
        abuse_detector.log_error(client_ip)
        observability_metrics.record_error("general_exception")
        return ChatResponse(
            response="I'm experiencing technical difficulties. Please try again.",
            session_id=session_id,
            debug_info=debug_info if config.debug_mode else None
        )

@router.post("/expand-knowledge")
@limiter.limit("10/hour")
async def expand_knowledge(
    request: KnowledgeExpansionRequest, 
    http_request: Request,
    x_admin_key: Optional[str] = Header(None)
):
    client_ip = get_remote_address(http_request)
    
    # Check if knowledge expansion is enabled
    if not config.expand_knowledge_enabled:
        logger.log_security_event("disabled_endpoint_access", client_ip, {
            "endpoint": "/expand-knowledge"
        })
        raise HTTPException(status_code=403, detail="Knowledge expansion is disabled")
    
    # Validate admin key
    if config.admin_api_key and x_admin_key != config.admin_api_key:
        logger.log_security_event("invalid_admin_key", client_ip, {
            "provided_key_length": len(x_admin_key) if x_admin_key else 0
        })
        raise HTTPException(status_code=401, detail="Invalid admin key")
    
    try:
        # Validate input length
        if len(request.raw_text) > config.max_context_length:
            raise HTTPException(status_code=400, detail="Text too long")
        
        # Process with Gemini with retries
        structured_knowledge = await _expand_knowledge_with_retry(
            gemini_client, 
            request.raw_text, 
            request.source_tag,
            request.domain
        )
        
        # Validate output
        validated_knowledge = SecurityValidator.validate_knowledge_json(structured_knowledge)
        
        if not validated_knowledge:
            logger.log_knowledge_expansion(
                request.source_tag, 
                len(request.raw_text), 
                0, 
                False
            )
            raise HTTPException(status_code=400, detail="No valid knowledge extracted")
        
        # Add domain tags to knowledge entries
        for entry in validated_knowledge:
            entry["domain"] = request.domain
        
        # Save to expanded knowledge
        knowledge_manager.add_expanded_knowledge(validated_knowledge)
        
        # Log successful expansion
        logger.log_knowledge_expansion(
            request.source_tag,
            len(request.raw_text),
            len(validated_knowledge),
            True
        )
        
        return {
            "status": "success", 
            "entries_added": len(validated_knowledge),
            "domain": request.domain
        }
        
    except HTTPException:
        observability_metrics.record_error("knowledge_expansion_http")
        raise
    except Exception as e:
        logger.log_api_error("knowledge_expansion", e, {
            "source_tag": request.source_tag,
            "text_length": len(request.raw_text),
            "domain": request.domain
        })
        observability_metrics.record_error("knowledge_expansion_general")
        raise HTTPException(status_code=500, detail="Knowledge expansion failed")

async def _get_response_with_retry(client, prompt: str, session_id: str):
    """Get response with retry logic and fallback"""
    last_error = None
    
    for attempt in range(config.max_retries):
        try:
            response, token_usage = await client.chat(prompt)
            return response, token_usage
        except Exception as e:
            last_error = e
            observability_metrics.record_api_failure("grok_api")
            if attempt < config.max_retries - 1:
                await asyncio.sleep(config.retry_delay * (attempt + 1))
            logger.log_api_error("grok_api", e, {
                "session_id": session_id,
                "attempt": attempt + 1
            })
    
    # Fallback response
    return "I'm having trouble connecting to my AI service. Please try again in a moment.", None

async def _expand_knowledge_with_retry(client, raw_text: str, source_tag: str, domain: str):
    """Expand knowledge with retry logic"""
    last_error = None
    
    for attempt in range(config.max_retries):
        try:
            return await client.expand_knowledge(raw_text, source_tag, domain)
        except Exception as e:
            last_error = e
            observability_metrics.record_api_failure("gemini_api")
            if attempt < config.max_retries - 1:
                await asyncio.sleep(config.retry_delay * (attempt + 1))
            logger.log_api_error("gemini_api", e, {
                "source_tag": source_tag,
                "domain": domain,
                "attempt": attempt + 1
            })
    
    raise last_error