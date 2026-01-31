from typing import List, Dict, Optional
from config import get_config
from logger import logger
import json

config = get_config()

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
    
    def add_message(self, session_id: str, user_message: str, bot_response: str):
        """Add message pair to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": self._get_timestamp()
        })
        
        # Trim if exceeds limits
        self._trim_conversation(session_id)
    
    def get_conversation_context(self, session_id: str, max_tokens: int = None) -> str:
        """Get conversation history as context string with token limits"""
        if session_id not in self.conversations:
            return ""
        
        max_tokens = max_tokens or config.conversation_token_limit
        conversation = self.conversations[session_id]
        
        # Build context from most recent messages
        context_parts = []
        estimated_tokens = 0
        
        for message in reversed(conversation):
            user_part = f"User: {message['user']}"
            bot_part = f"Assistant: {message['bot']}"
            
            # Rough token estimation (4 chars ≈ 1 token)
            part_tokens = (len(user_part) + len(bot_part)) // 4
            
            if estimated_tokens + part_tokens > max_tokens:
                break
            
            context_parts.insert(0, user_part)
            context_parts.insert(0, bot_part)
            estimated_tokens += part_tokens
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _trim_conversation(self, session_id: str):
        """Trim conversation to stay within limits"""
        if session_id not in self.conversations:
            return
        
        conversation = self.conversations[session_id]
        
        # Keep only recent messages
        if len(conversation) > config.max_conversation_history:
            self.conversations[session_id] = conversation[-config.max_conversation_history:]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

# Global conversation manager
conversation_manager = ConversationManager()