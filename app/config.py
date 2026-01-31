import os
from typing import Optional
from pydantic import BaseSettings

class AppConfig(BaseSettings):
    # API Keys
    grok_api_key: str
    gemini_api_key: str
    admin_api_key: Optional[str] = None
    
    # Server Configuration
    port: int = 8000
    host: str = "0.0.0.0"
    debug_mode: bool = False
    
    # AI Provider Configuration
    llm_provider: str = "grok"
    grok_model: str = "grok-beta"
    gemini_model: str = "gemini-pro"
    fallback_provider: Optional[str] = None
    
    # File Paths
    knowledge_dir: str = "knowledge"
    rules_dir: str = "rules"
    logs_dir: str = "logs"
    
    # Security Settings
    max_message_length: int = 2000
    max_context_length: int = 8000
    max_knowledge_entries: int = 10
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    expand_knowledge_enabled: bool = True
    
    # API Settings
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Widget Settings
    allowed_origins: str = "*"
    widget_session_timeout: int = 3600
    widget_version: str = "1.0.0"
    
    # Conversation Management
    max_conversation_history: int = 10
    conversation_token_limit: int = 4000
    
    # Logging
    log_token_usage: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_required_keys(self):
        """Validate that required API keys are present"""
        if not self.grok_api_key:
            raise ValueError("GROK_API_KEY is required")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")
        if self.expand_knowledge_enabled and not self.admin_api_key:
            raise ValueError("ADMIN_API_KEY is required when expand_knowledge_enabled=True")

# Global config instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get application configuration"""
    return config