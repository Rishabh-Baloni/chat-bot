from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import httpx
import asyncio
import uuid
import time

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
                        {"role": "system", "content": "You are a helpful AI assistant. Be friendly and concise."},
                        {"role": "user", "content": message}
                    ],
                    "model": "llama3-8b-8192",
                    "temperature": 0.7,
                    "max_tokens": 500
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