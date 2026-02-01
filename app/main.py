from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import httpx
import asyncio
import uuid
import time
from dotenv import load_dotenv

# Robust path handling for .env loading
basedir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(basedir)
load_dotenv(dotenv_path=os.path.join(parent_dir, ".env"), override=False)
load_dotenv(dotenv_path=os.path.join(basedir, ".env"), override=False)

app = Flask(__name__)
CORS(app)

# Configuration
GROK_API_KEY = os.getenv("GROK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Simple conversation memory
conversations = {}
conversation_stages = {}

@app.route('/')
def root():
    return {"message": "Chatbot Engine Running", "widget_url": "/widget/widget.js"}

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "services": {
            "grok_api": bool(GROK_API_KEY),
            "gemini_api": bool(GEMINI_API_KEY)
        }
    }

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        # Get conversation history and stage
        if session_id not in conversations:
            conversations[session_id] = []
            conversation_stages[session_id] = "greeting"
        
        current_stage = conversation_stages[session_id]
        
        # Add user message to history
        conversations[session_id].append(f"User: {message}")
        
        # Build context from conversation history (use full history for better context)
        conversation_context = "\n".join(conversations[session_id])
        
        # Determine next stage based on current stage and user input
        total_user_messages = len([msg for msg in conversations[session_id] if msg.startswith("User:")])
        next_stage = determine_next_stage(current_stage, message, conversation_context, total_user_messages)
        
        # Handle Session Reset
        if next_stage == "greeting" and (current_stage == "conclusion" or current_stage == "goodbye"):
            # Archive old conversation or just clear it
            conversations[session_id] = [f"User: {message}"] # Keep just the new greeting
            conversation_context = f"User: {message}" # Reset context for the API call
            
            # Important: Ensure we don't accidentally pull in old relevant knowledge
            # (Though call_groq_api re-evaluates relevant_knowledge based on current message anyway)
            
        conversation_stages[session_id] = next_stage
        
        # Simple chat response using httpx
        response = call_groq_api(message, conversation_context, current_stage, next_stage)
        
        # Add bot response to conversation history
        conversations[session_id].append(f"Assistant: {response}")
        
        # Add stage info for debugging
        debug_info = {"current_stage": current_stage, "next_stage": next_stage} if os.getenv("DEBUG") else None
        
        return jsonify({
            "response": response,
            "session_id": session_id,
            "version": "1.0.0",
            "stage": next_stage,
            "debug": debug_info
        })
        
    except Exception as e:
        print(f"Chat Endpoint Error: {str(e)}") # Log to console
        return jsonify({
            "response": f"I'm experiencing technical difficulties. Please try again. Error: {str(e)}",
            "session_id": session_id,
            "version": "1.0.0"
        })

def determine_next_stage(current_stage, message, context, user_message_count):
    """Determine conversation flow stage using smart logic"""
    message_lower = message.lower().strip().strip('.,!?')
    
    # Emergency keywords - skip to conclusion
    emergency_keywords = ["chest pain", "can't breathe", "severe bleeding", "emergency"]
    if any(keyword in message_lower for keyword in emergency_keywords):
        return "emergency_conclusion"
    
    # Restart detection - if user greets again after conclusion/goodbye, reset
    # Check for restart BEFORE length checks to allow resetting long conversations
    restart_keywords = ["hi", "hello", "hey", "start over", "restart", "new chat", "greetings"]
    
    if current_stage == "conclusion" or current_stage == "goodbye":
        is_restart = False
        for keyword in restart_keywords:
             # Check if keyword is exactly the message OR keyword is in the message words
             if keyword == message_lower or keyword in message_lower.split():
                 is_restart = True
                 break
        
        if is_restart:
            return "greeting"
    
    # Prioritize treatment requests - if user asks for treatment, give it immediately
    treatment_keywords = ["treatment", "cure", "medicine", "remedy", "what should i do", "how to treat", "how to fix", "tell me the treatment"]
    if any(keyword in message_lower for keyword in treatment_keywords):
        return "conclusion"
    
    # Handle confusion - if user says "what?" they need clarification, not new conversation
    confusion_words = ["what", "what?", "huh", "huh?", "confused", "don't understand"]
    if any(word in message_lower for word in confusion_words) and len(context.split('\n')) > 1:
        return "conclusion"  # Provide summary instead of resetting
    
    # User wants conclusion - detect frustration or request for advice
    conclusion_signals = [
        "what" in message_lower and ("do" in message_lower or "should" in message_lower),
        "help" in message_lower and len(message.split()) <= 3,
        "advice" in message_lower,
        "recommend" in message_lower,
        "serious" in message_lower and "fix" in message_lower,
        "joking" in message_lower,
        message_lower in ["nothing", "no", "nah", "nahhhh", "none", "ok", "okay", "fine"]
    ]
    
    # Force conclusion if user seems frustrated or conversation is long
    # Only force conclusion if we are not already in conclusion or goodbye stages
    if (any(conclusion_signals) or user_message_count >= 5) and current_stage not in ["conclusion", "goodbye"]:
        return "conclusion"
    
    # Goodbye detection
    goodbye_keywords = ["bye", "goodbye", "thanks", "thank you", "that's all"]
    if any(keyword in message_lower for keyword in goodbye_keywords):
        return "goodbye"

    # Smart stage progression based on information gathered
    if current_stage == "greeting":
        return "symptom_gathering"
    elif current_stage == "symptom_gathering":
        # Move to follow-up after basic info is gathered
        if user_message_count >= 2:
            return "follow_up_questions"
        return "symptom_gathering"
    elif current_stage == "follow_up_questions":
        # Move to conclusion after sufficient follow-up
        if user_message_count >= 4:
            return "conclusion"
        return "follow_up_questions"
    elif current_stage == "conclusion":
        return "goodbye"
    else:
        return "greeting"

def call_groq_api(message, conversation_context="", current_stage="greeting", next_stage="symptom_gathering"):
    try:
        # Load and use knowledge base
        relevant_knowledge = ""
        try:
            with open('../knowledge/core_knowledge.json', 'r', encoding='utf-8') as f:
                knowledge_data = json.load(f)
                # Find relevant knowledge entries
                for entry in knowledge_data:
                    keywords = entry.get('symptoms_or_keywords', [])
                    if any(keyword.lower() in message.lower() for keyword in keywords):
                        relevant_knowledge += f"\nRelevant info: {entry.get('response_guidance', '')}"
                        break  # Use first match
        except:
            pass
        
        # Stage-based system prompts
        stage_prompts = {
            "greeting": "You are a friendly AI health assistant. Greet the user warmly and ask what health concerns they have today. Keep it brief and welcoming.",
            
            "symptom_gathering": f"""You are gathering initial symptom information. 

Conversation so far:
{conversation_context}

{relevant_knowledge}

Ask specific questions about:
- Main symptoms and location
- Duration (how long)
- Severity (1-10 scale)
- What makes it better/worse

Keep responses under 2 sentences. Ask ONE specific question.""",
            
            "follow_up_questions": f"""You are gathering detailed follow-up information.

Conversation so far:
{conversation_context}

{relevant_knowledge}

Ask about:
- Associated symptoms
- Triggers or patterns
- Previous treatments tried
- Impact on daily life

Keep responses under 2 sentences. Ask ONE specific follow-up question.""",
            
            "conclusion": f"""You are providing final medical assessment and recommendations.

Conversation so far:
{conversation_context}

{relevant_knowledge}

Analyze the conversation and provide a structured response using Markdown:
1. **Summary of Key Symptoms**: Briefly list the symptoms mentioned.
2. **Most Likely Causes**: Based on the symptoms, list potential causes.
3. **Actionable Recommendations**: Provide specific advice.
4. **When to Seek Medical Care**: Clear warning signs.

Format your response with clear headings (e.g., ## Summary) and bullet points. Be concise but complete. End with a caring message.""",
            
            "emergency_conclusion": f"""EMERGENCY RESPONSE NEEDED.

Conversation so far:
{conversation_context}

{relevant_knowledge}

Provide:
1. 'These symptoms require immediate medical attention.'
2. 'Please call emergency services or go to the nearest emergency room.'
3. Brief explanation why it's urgent
4. 'Do not wait - seek help now.'""",
            
            "goodbye": "Thank the user for using the health assistant. Wish them well and remind them to seek professional medical care for serious concerns. Keep it brief and caring."
        }
        
        system_prompt = stage_prompts.get(next_stage, stage_prompts["greeting"])
        
        with httpx.Client() as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "model": "llama-3.1-8b-instant",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            print(f"Groq API Status: {response.status_code}")  # Debug log
            print(f"Groq API Response: {response.text[:200]}")  # Debug log
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "I received an empty response. Please try again."
            elif response.status_code == 401:
                return "API authentication failed. Please check the API key."
            elif response.status_code == 429:
                return "I'm currently busy. Please try again in a moment."
            else:
                return f"API returned status {response.status_code}. Please try again."
                
    except httpx.TimeoutException:
        return "Request timed out. Please try again."
    except Exception as e:
        print(f"Groq API Error: {str(e)}")  # Debug log
        return f"Technical error: {str(e)[:100]}. Please try again."

@app.route('/widget/<path:filename>')
def serve_widget(filename):
    return send_from_directory('../widget', filename)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
