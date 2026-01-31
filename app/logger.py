import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from operational_safety import secret_masker

class ChatbotLogger:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configure loggers
        self.setup_loggers()
    
    def setup_loggers(self):
        """Setup different loggers for different purposes"""
        
        # Chat logger - NO sensitive data
        self.chat_logger = logging.getLogger('chatbot.chat')
        self.chat_logger.setLevel(logging.INFO)
        chat_handler = logging.FileHandler(self.logs_dir / 'chat.log')
        chat_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.chat_logger.addHandler(chat_handler)
        
        # API error logger - masked secrets
        self.error_logger = logging.getLogger('chatbot.errors')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = logging.FileHandler(self.logs_dir / 'errors.log')
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.error_logger.addHandler(error_handler)
        
        # Knowledge expansion logger
        self.knowledge_logger = logging.getLogger('chatbot.knowledge')
        self.knowledge_logger.setLevel(logging.INFO)
        knowledge_handler = logging.FileHandler(self.logs_dir / 'knowledge.log')
        knowledge_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.knowledge_logger.addHandler(knowledge_handler)
        
        # Security/abuse logger
        self.security_logger = logging.getLogger('chatbot.security')
        self.security_logger.setLevel(logging.WARNING)
        security_handler = logging.FileHandler(self.logs_dir / 'security.log')
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.security_logger.addHandler(security_handler)
    
    def log_chat(self, session_id: str, user_message: str, bot_response: str, 
                 processing_time: float, ip_address: str = "unknown"):
        """Log chat interactions - NO sensitive content"""
        log_data = {
            'session_id': session_id[:8] + '***',  # Partial session ID only
            'user_message_length': len(user_message),
            'bot_response_length': len(bot_response),
            'processing_time': processing_time,
            'ip_hash': hash(ip_address) % 10000,  # Hash IP for privacy
            'timestamp': datetime.utcnow().isoformat()
        }
        self.chat_logger.info(json.dumps(log_data))
    
    def log_api_error(self, api_name: str, error: Exception, context: Dict[str, Any]):
        """Log API errors with masked secrets"""
        # Mask secrets in context
        safe_context = {}
        for key, value in context.items():
            if isinstance(value, str):
                safe_context[key] = secret_masker.mask_secrets(value)
            else:
                safe_context[key] = value
        
        log_data = {
            'api': api_name,
            'error_type': type(error).__name__,
            'error_message': secret_masker.mask_secrets(str(error)),
            'context': safe_context,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.error_logger.error(json.dumps(log_data))
    
    def log_knowledge_expansion(self, source_tag: str, raw_text_length: int, 
                               entries_created: int, success: bool):
        """Log knowledge expansion operations"""
        log_data = {
            'source_tag': source_tag,
            'raw_text_length': raw_text_length,
            'entries_created': entries_created,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.knowledge_logger.info(json.dumps(log_data))
    
    def log_security_event(self, event_type: str, ip_address: str, details: Dict[str, Any]):
        """Log security events and abuse attempts"""
        log_data = {
            'event_type': event_type,
            'ip_hash': hash(ip_address) % 10000,  # Hash IP for privacy
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.security_logger.warning(json.dumps(log_data))
    
    def log_observability(self, metrics: Dict[str, Any]):
        """Log system metrics for observability"""
        self.chat_logger.info(f"METRICS: {json.dumps(metrics)}")

# Global logger instance
logger = ChatbotLogger()