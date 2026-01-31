import re
import time
from typing import Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from config import get_config

config = get_config()

class SecretMasker:
    """Utility to mask secrets in logs and debug output"""
    
    SECRET_PATTERNS = [
        r'(api[_-]?key["\s]*[:=]["\s]*)([a-zA-Z0-9_-]{20,})',
        r'(token["\s]*[:=]["\s]*)([a-zA-Z0-9_.-]{20,})',
        r'(password["\s]*[:=]["\s]*)([^\s"]{8,})',
        r'(secret["\s]*[:=]["\s]*)([a-zA-Z0-9_-]{16,})',
        r'Bearer\s+([a-zA-Z0-9_.-]{20,})',
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI-style keys
        r'xai-[a-zA-Z0-9]{20,}', # Grok-style keys
    ]
    
    @staticmethod
    def mask_secrets(text: str) -> str:
        """Mask secrets in text for safe logging"""
        if not text:
            return text
        
        masked_text = text
        for pattern in SecretMasker.SECRET_PATTERNS:
            masked_text = re.sub(pattern, r'\1***MASKED***', masked_text, flags=re.IGNORECASE)
        
        return masked_text

class AbuseDetector:
    """Detect and log abuse patterns"""
    
    def __init__(self):
        self.ip_requests = defaultdict(deque)
        self.ip_errors = defaultdict(int)
        self.suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'document\.',
            r'window\.',
            r'alert\(',
            r'prompt\(',
            r'confirm\(',
        ]
    
    def check_request_abuse(self, ip: str, user_agent: str = "") -> bool:
        """Check if request shows abuse patterns"""
        now = time.time()
        
        # Clean old requests (last hour)
        cutoff = now - 3600
        while self.ip_requests[ip] and self.ip_requests[ip][0] < cutoff:
            self.ip_requests[ip].popleft()
        
        # Add current request
        self.ip_requests[ip].append(now)
        
        # Check rate (more than 100 requests per hour)
        if len(self.ip_requests[ip]) > 100:
            return True
        
        # Check for suspicious user agent patterns
        if user_agent and any(pattern in user_agent.lower() for pattern in ['bot', 'crawler', 'spider', 'scraper']):
            if len(self.ip_requests[ip]) > 10:  # Lower threshold for bots
                return True
        
        return False
    
    def check_message_abuse(self, message: str) -> bool:
        """Check if message contains suspicious patterns"""
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in self.suspicious_patterns)
    
    def log_error(self, ip: str):
        """Log error for IP tracking"""
        self.ip_errors[ip] += 1
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP should be blocked due to errors"""
        return self.ip_errors[ip] > 50  # Block after 50 errors

class ObservabilityMetrics:
    """Track system metrics for observability"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.api_failures = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        self.response_timestamps = deque(maxlen=1000)
        self.start_time = time.time()
    
    def record_request(self, response_time: float):
        """Record successful request"""
        self.request_count += 1
        self.response_times.append(response_time)
        self.response_timestamps.append(time.time())
    
    def record_error(self, error_type: str = "general"):
        """Record error"""
        self.error_count += 1
    
    def record_api_failure(self, api_name: str):
        """Record API failure"""
        self.api_failures[api_name] += 1
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        uptime = time.time() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "avg_response_time": avg_response_time,
            "api_failures": dict(self.api_failures),
            "requests_per_minute": len([t for t in self.response_timestamps if time.time() - t < 60])
        }

class MedicalSafetyEnforcer:
    """Enforce medical disclaimers and safety"""
    
    MEDICAL_KEYWORDS = [
        'symptom', 'diagnosis', 'treatment', 'medicine', 'drug', 'medication',
        'disease', 'illness', 'condition', 'pain', 'fever', 'infection',
        'doctor', 'physician', 'hospital', 'clinic', 'medical', 'health',
        'therapy', 'surgery', 'prescription', 'dosage', 'side effect'
    ]
    
    MEDICAL_DISCLAIMER = """
⚠️ MEDICAL DISCLAIMER: This AI assistant provides general information only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for medical concerns. Never disregard professional medical advice or delay seeking it because of information from this AI.
"""
    
    @staticmethod
    def requires_medical_disclaimer(message: str, knowledge_entries: List[Dict] = None) -> bool:
        """Check if medical disclaimer is required"""
        message_lower = message.lower()
        
        # Check message content
        if any(keyword in message_lower for keyword in MedicalSafetyEnforcer.MEDICAL_KEYWORDS):
            return True
        
        # Check knowledge entries
        if knowledge_entries:
            for entry in knowledge_entries:
                if entry.get('domain') == 'medical' or entry.get('risk_level') == 'high':
                    return True
                
                topic = entry.get('topic', '').lower()
                if any(keyword in topic for keyword in MedicalSafetyEnforcer.MEDICAL_KEYWORDS):
                    return True
        
        return False
    
    @staticmethod
    def add_medical_disclaimer(response: str) -> str:
        """Add medical disclaimer to response"""
        return response + MedicalSafetyEnforcer.MEDICAL_DISCLAIMER

# Global instances
secret_masker = SecretMasker()
abuse_detector = AbuseDetector()
observability_metrics = ObservabilityMetrics()
medical_safety = MedicalSafetyEnforcer()
