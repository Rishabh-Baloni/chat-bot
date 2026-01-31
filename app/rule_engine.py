from pathlib import Path
from typing import str

class RuleEngine:
    def __init__(self):
        self.rules_dir = Path("rules")
        self.rules_file = self.rules_dir / "rules.txt"
        
        # Ensure rules directory exists
        self.rules_dir.mkdir(exist_ok=True)
        
        # Initialize rules file if it doesn't exist
        if not self.rules_file.exists():
            self._create_default_rules()
    
    def _create_default_rules(self):
        """Create default rules file"""
        default_rules = """# Chatbot Rules

## Core Behavior
- Always be helpful and accurate
- If you don't know something, say so
- Use the provided knowledge base to answer questions
- Be concise but thorough

## Safety Guidelines
- Never provide medical advice - always recommend consulting professionals
- Don't make definitive diagnoses
- Include appropriate disclaimers when discussing health topics

## Response Format
- Use clear, easy-to-understand language
- Structure responses with bullet points when helpful
- Always cite knowledge sources when available
"""
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            f.write(default_rules)
    
    def load_rules(self) -> str:
        """Load rules from rules.txt file"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self._create_default_rules()
            return self.load_rules()
    
    def update_rules(self, new_rules: str):
        """Update rules file with new content"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            f.write(new_rules)