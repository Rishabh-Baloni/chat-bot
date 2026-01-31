# Self-Hosted AI Chatbot Engine

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Rishabh-Baloni/chat-bot)

A complete self-hosted chatbot solution with embeddable web widget. Uses Groq API for fast AI responses and Gemini API for knowledge expansion.

## ✨ Features

- 🤖 **Dual AI System**: Groq for chat, Gemini for knowledge processing
- 🌐 **Embeddable Widget**: One-line integration for any website
- 📚 **Smart Knowledge Base**: JSON-based with auto-expansion
- 🎨 **Fully Customizable**: Rules, appearance, and behavior
- 🚀 **Deploy Ready**: Optimized for Render free tier
- 🔐 **Self-Hosted**: Your API keys, your data

## 🚀 Quick Start

**New to this?** → [Setup Guide](SETUP.md)  
**Want to customize?** → [Customization Guide](CUSTOMIZATION.md)

### 1-Minute Deploy
1. Get API keys: [Groq](https://console.groq.com/keys) + [Gemini](https://aistudio.google.com/app/apikey)
2. Fork this repo
3. Deploy to [Render](https://render.com) 
4. Set environment variables
5. Embed: `<script src="https://your-app.onrender.com/widget/widget.js"></script>`

## 📋 What You Get

### Core Files
```
├── app/
│   ├── main.py              # Flask API server
│   └── operational_safety.py # Security utilities
├── widget/
│   ├── widget.js            # Embeddable chat widget
│   └── widget.css           # Widget styling
├── knowledge/
│   ├── core_knowledge.json  # Your knowledge base
│   └── expanded_knowledge.json # AI-generated entries
├── rules/
│   └── rules.txt            # Bot behavior rules
├── requirements.txt         # Python dependencies
└── runtime.txt             # Python version
```

### API Endpoints
- `POST /chat` - Send messages to bot
- `POST /expand-knowledge` - Add knowledge from text
- `GET /health` - Check system status
- `GET /widget/widget.js` - Embeddable widget

## 🎯 Use Cases

- **Customer Support**: 24/7 automated help desk
- **Lead Generation**: Qualify prospects on your website  
- **FAQ Bot**: Answer common questions instantly
- **Product Assistant**: Help users find what they need
- **Internal Tools**: Employee self-service portal

## 🛠️ Customization Examples

### Change Bot Personality
```txt
# Edit rules/rules.txt
You are a friendly assistant for [YOUR COMPANY].
Always be helpful and professional.
If unsure, say "Let me connect you with a human."
```

### Add Your Knowledge
```json
// Edit knowledge/core_knowledge.json
{
  "topic": "Business Hours",
  "symptoms_or_keywords": ["hours", "open", "closed"],
  "response_guidance": "We're open Monday-Friday 9AM-6PM EST",
  "risk_level": "low",
  "confidence": 1.0
}
```

### Style the Widget
```html
<script>
window.ChatbotConfig = {
  buttonText: '💬 Help',
  headerText: 'Your Company Support',
  theme: 'dark',
  position: 'bottom-left'
};
</script>
```

## 🔧 Local Development

```bash
# 1. Clone and setup
git clone https://github.com/Rishabh-Baloni/chat-bot
cd your-repo
cp .env.example .env
# Edit .env with your API keys

# 2. Install and run
pip install -r requirements.txt
cd app && python main.py

# 3. Test at http://localhost:8000
```

## 📊 Architecture

```
User Website → Widget → Your Render App → Groq API → Response
                    ↓
               Knowledge Base + Rules
```

## 🔒 Security Features

- Input sanitization and validation
- Rate limiting and abuse detection  
- Medical/legal disclaimer enforcement
- Prompt injection protection
- Session management

## 💰 Cost Estimate

- **Render Hosting**: Free tier (750 hours/month)
- **Groq API**: ~$0.10 per 1M tokens (very cheap)
- **Gemini API**: Free tier (15 requests/minute)
- **Total**: Essentially free for most use cases

## 🆘 Support

1. **Setup Issues**: Check [SETUP.md](SETUP.md)
2. **Customization**: See [CUSTOMIZATION.md](CUSTOMIZATION.md)  
3. **API Problems**: Verify keys in Render environment
4. **Widget Issues**: Check browser console for errors

## 📄 License

MIT License - Use freely for personal and commercial projects.

---

**Ready to deploy?** → [Get Started](SETUP.md) | **Questions?** → [Open an Issue](../../issues)