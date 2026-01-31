# 🚀 DEPLOYMENT GUIDE - Step by Step

## ✅ STEP 1: You Have Everything Ready

**API Keys Required:**
- ✅ Groq API Key (from console.groq.com)
- ✅ Gemini API Key (from console.cloud.google.com)

**Project Structure:**
- ✅ Backend code in `app/`
- ✅ Widget files in `widget/`
- ✅ Knowledge files in `knowledge/`
- ✅ Rules files in `rules/`
- ✅ `requirements.txt`
- ✅ `.env.example`

## 🚀 STEP 2: Deploy to Render

### 2.1 Go to Render
1. Open https://render.com
2. Sign up/Login with GitHub
3. Click **"New"** → **"Web Service"**
4. Connect your GitHub repository

### 2.2 Configure Render Settings

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
cd app && python main.py
```

**Environment Variables (CRITICAL):**
```
GROK_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG_MODE=false
EXPAND_KNOWLEDGE_ENABLED=false
LOG_TOKEN_USAGE=true
ADMIN_API_KEY=secure_admin_key_12345
PORT=10000
```

### 2.3 Deploy
1. Click **"Create Web Service"**
2. Wait 2-5 minutes for first deployment

## ✅ STEP 3: Test Your Deployment

### 3.1 Test Health Endpoint
Open in browser:
```
https://your-app-name.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "services": {
    "grok_api": true,
    "gemini_api": true,
    "knowledge_system": true,
    "rules_system": true
  }
}
```

### 3.2 Test Chat API
Use curl or Postman:
```bash
curl -X POST https://your-app-name.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## 🎯 STEP 4: Test Widget Integration

### 4.1 Create Test HTML File
```html
<!DOCTYPE html>
<html>
<head><title>Widget Test</title></head>
<body>
    <h1>My Website</h1>
    <script src="https://your-app-name.onrender.com/widget/widget.js"></script>
</body>
</html>
```

### 4.2 Test Widget
1. Open the HTML file
2. Click chat button (bottom-right)
3. Send test message
4. Verify response

## 🔧 STEP 5: Customize Your Chatbot

### 5.1 Update Rules (Day 1)
Edit `rules/rules.txt`:
```
# My Chatbot Rules

## Personality
- Be friendly and professional
- Use a helpful tone
- Keep responses concise

## Domain Knowledge
- I help with [YOUR DOMAIN]
- I provide accurate information
- I always include disclaimers when needed
```

### 5.2 Add Core Knowledge (Day 2-3)
Edit `knowledge/core_knowledge.json`:
```json
[
  {
    "topic": "Your Main Topic",
    "symptoms_or_keywords": ["keyword1", "keyword2", "help"],
    "response_guidance": "Explain your main service/product clearly",
    "risk_level": "low",
    "confidence": "0.9",
    "source": "core"
  }
]
```

## 🎉 SUCCESS CHECKLIST

You're done when:
- ✅ Health endpoint returns "healthy"
- ✅ Chat API responds to messages
- ✅ Widget loads and works on test page
- ✅ Responses match your rules/knowledge
- ✅ No crashes or errors

## 🔒 PRODUCTION LOCK

After testing, confirm these settings:
```
DEBUG_MODE=false
EXPAND_KNOWLEDGE_ENABLED=false
```

## 📝 Your Render URL
After deployment, your URLs will be:
- **API**: `https://your-app-name.onrender.com`
- **Widget**: `https://your-app-name.onrender.com/widget/widget.js`
- **Health**: `https://your-app-name.onrender.com/health`

## 🚀 You're Live!
Your chatbot is now deployed and ready to embed on any website!