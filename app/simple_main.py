from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import httpx
import asyncio
import uuid
import time
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=False)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)

app = Flask(__name__)
CORS(app)

# Configuration
GROK_API_KEY = os.getenv("GROK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
        
        # Simple chat response using httpx
        response = asyncio.run(call_groq_api(message))
        
        return jsonify({
            "response": response,
            "session_id": session_id,
            "version": "1.0.0"
        })
        
    except Exception as e:
        return jsonify({
            "response": "I'm experiencing technical difficulties. Please try again.",
            "session_id": session_id,
            "version": "1.0.0"
        })

async def call_groq_api(message):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": message}
                    ],
                    "model": "llama3-8b-8192",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return "I'm having trouble connecting. Please try again."
                
    except Exception:
        return "I'm experiencing technical difficulties. Please try again."

@app.route('/widget/<path:filename>')
def serve_widget(filename):
    return send_from_directory('../widget', filename)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
