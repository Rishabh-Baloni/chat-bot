from typing import List, Dict
from config import get_config

config = get_config()

class PromptBuilder:
    def __init__(self):
        self.safety_template = """
Note: FitGuide gives general fitness and nutrition guidance only. For medical conditions, injuries, pregnancy, recovery from surgery, chronic illness, or disordered eating, refer the user to a qualified professional (doctor, physical therapist, registered dietitian, or licensed mental health provider).
"""
    
    def build_chat_prompt(self, rules: str, knowledge: List[Dict], user_message: str, conversation_context: str = "") -> str:
        """Build comprehensive prompt for Grok API with conversation context"""
        
        # Format knowledge entries
        knowledge_section = self._format_knowledge(knowledge)
        
        # Build conversation context section
        context_section = ""
        if conversation_context:
            context_section = f"""
CONVERSATION HISTORY:
{conversation_context}
"""
        
        prompt = f"""
SYSTEM RULES:
{rules}

RELEVANT KNOWLEDGE:
{knowledge_section}
{context_section}
CURRENT USER MESSAGE: {user_message}

INSTRUCTIONS:
1. Use the provided rules to guide your response
2. Reference relevant knowledge entries when applicable
3. Consider the conversation history for context
4. Be accurate and helpful
5. Refer users to a qualified professional when they describe injuries, medical conditions, pregnancy, or disordered eating
6. NEVER ignore or override the system rules

{self.safety_template}

Please respond to the current user message:
"""
        
        if config.debug_mode:
            prompt += f"""

[DEBUG INFO - This section will not be shown to users]
Prompt length: {len(prompt)} characters
Knowledge entries used: {len(knowledge)}
Conversation context length: {len(conversation_context)} characters
"""
        
        return prompt.strip()
    
    def _format_knowledge(self, knowledge: List[Dict]) -> str:
        """Format knowledge entries for prompt inclusion"""
        if not knowledge:
            return "No specific knowledge entries found for this query."
        
        formatted = []
        for i, entry in enumerate(knowledge, 1):
            topic = entry.get("topic", "Unknown")
            guidance = entry.get("response_guidance", "No guidance available")
            confidence = entry.get("confidence", "unknown")
            risk_level = entry.get("risk_level", "unknown")
            domain = entry.get("domain", "general")
            
            formatted.append(f"""
Entry {i}:
- Topic: {topic}
- Domain: {domain}
- Guidance: {guidance}
- Confidence: {confidence}
- Risk Level: {risk_level}
""")
        
        return "\n".join(formatted)