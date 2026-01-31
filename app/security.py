import re
import json
from typing import Dict, List, Any
from pydantic import BaseModel, ValidationError

class SecurityConfig:
    MAX_MESSAGE_LENGTH = 2000
    MAX_CONTEXT_LENGTH = 8000
    MAX_KNOWLEDGE_ENTRIES = 10
    BLOCKED_PATTERNS = [
        r'ignore\s+previous\s+instructions',
        r'system\s*:',
        r'assistant\s*:',
        r'<\s*system\s*>',
        r'override\s+rules',
        r'forget\s+everything',
        r'new\s+instructions',
    ]

class KnowledgeEntrySchema(BaseModel):
    topic: str
    symptoms_or_keywords: List[str]
    response_guidance: str
    risk_level: str
    confidence: str
    source: str

class SecurityValidator:
    @staticmethod
    def sanitize_user_input(message: str) -> str:
        """Sanitize user input to prevent prompt injection"""
        if len(message) > SecurityConfig.MAX_MESSAGE_LENGTH:
            message = message[:SecurityConfig.MAX_MESSAGE_LENGTH]
        
        # Remove potential injection patterns
        for pattern in SecurityConfig.BLOCKED_PATTERNS:
            message = re.sub(pattern, '[FILTERED]', message, flags=re.IGNORECASE)
        
        # Remove excessive whitespace and control characters
        message = re.sub(r'\s+', ' ', message).strip()
        message = ''.join(char for char in message if ord(char) >= 32 or char in '\n\t')
        
        return message
    
    @staticmethod
    def validate_knowledge_json(data: Any) -> List[Dict]:
        """Validate Gemini output against knowledge schema"""
        if not isinstance(data, list):
            data = [data] if isinstance(data, dict) else []
        
        validated_entries = []
        for entry in data:
            try:
                # Validate against schema
                validated_entry = KnowledgeEntrySchema(**entry)
                
                # Additional validation
                if (validated_entry.confidence.replace('.', '').isdigit() and 
                    0.0 <= float(validated_entry.confidence) <= 1.0 and
                    validated_entry.risk_level.lower() in ['low', 'medium', 'high']):
                    
                    validated_entries.append(validated_entry.dict())
                    
            except (ValidationError, ValueError, TypeError):
                continue  # Skip invalid entries
        
        return validated_entries
    
    @staticmethod
    def limit_context_size(prompt: str) -> str:
        """Ensure prompt doesn't exceed context limits"""
        if len(prompt) > SecurityConfig.MAX_CONTEXT_LENGTH:
            # Truncate from middle, keep beginning and end
            start_len = SecurityConfig.MAX_CONTEXT_LENGTH // 3
            end_len = SecurityConfig.MAX_CONTEXT_LENGTH // 3
            
            start = prompt[:start_len]
            end = prompt[-end_len:]
            
            return f"{start}\n\n[CONTEXT TRUNCATED]\n\n{end}"
        
        return prompt