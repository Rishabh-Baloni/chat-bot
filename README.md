# Self-Hosted Knowledge-Driven Chatbot Engine

A self-hostable chatbot system with embeddable web widget that uses Grok API for chat reasoning and Gemini API for knowledge expansion.

## Features

- 🤖 **Dual AI System**: Grok for real-time chat, Gemini for knowledge processing
- 🌐 **Embeddable Widget**: Single script tag integration for any website
- 📚 **Knowledge Management**: JSON-based knowledge system with expansion capabilities
- 🔧 **Rule Engine**: Customizable behavior rules
- 🚀 **Render Ready**: Optimized for Render free tier deployment
- 🔐 **Self-Hosted**: Use your own API keys, no shared resources

## Quick Start

### 1. Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

1. Fork this repository
2. Connect to Render
3. Set environment variables (see below)
4. Deploy!

### 2. Environment Variables

```bash
GROK_API_KEY=your_grok_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
```

### 3. Embed Widget

Add to any website:

```html
<script src="https://your-render-app.onrender.com/widget/widget.js"></script>
```

## API Endpoints

### Chat
```bash
POST /chat
{
  "message": "Hello!",
  "session_id": "optional"
}
```

### Expand Knowledge
```bash
POST /expand-knowledge
{
  "raw_text": "Information to process",
  "source_tag": "source_name"
}
```

## Knowledge System

### Core Knowledge (`knowledge/core_knowledge.json`)
Static, verified knowledge entries.

### Expanded Knowledge (`knowledge/expanded_knowledge.json`)
Gemini-generated structured entries.

### Knowledge Entry Format
```json
{
  "topic": "Topic name",
  "symptoms_or_keywords": ["keyword1", "keyword2"],
  "response_guidance": "How to respond about this topic",
  "risk_level": "low/medium/high",
  "confidence": "0.0-1.0",
  "source": "source_tag"
}
```

## Rules System

Edit `rules/rules.txt` to customize chatbot behavior:

- Core behavior guidelines
- Safety rules
- Response formatting
- Domain-specific instructions

## Local Development

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run Server**
```bash
cd app
python main.py
```

4. **Test Widget**
Create test HTML file:
```html
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Test Page</h1>
    <script src="http://localhost:8000/widget/widget.js"></script>
</body>
</html>
```

## Architecture

```
User Website
 ↓
Embeds Chat Widget JS
 ↓
Widget Calls Your Render Backend
 ↓
Backend Loads: Rules + Knowledge
 ↓
Backend Calls Grok API
 ↓
Returns Chat Response
```

## AI Model Usage

### Grok API (Primary Chat)
- Natural conversation
- Context reasoning
- Rule following
- Knowledge-grounded answers

### Gemini API (Knowledge Processing)
- Single-prompt knowledge expansion
- Structured data extraction
- Confidence scoring
- Risk assessment

## Customization

### Adding Knowledge
1. **Manual**: Edit `knowledge/core_knowledge.json`
2. **API**: Use `/expand-knowledge` endpoint
3. **Bulk**: Process text files through Gemini

### Updating Rules
Edit `rules/rules.txt` with your specific guidelines.

### Widget Styling
Modify `widget/widget.css` for custom appearance.

## Deployment Notes

### Render Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd app && python main.py`
- **Environment**: Python 3.9+

### Performance
- Chat response: <5 seconds (excluding cold start)
- Widget load: <1 second
- Knowledge expansion: Variable (depends on text size)

## Security

- Rate limiting implemented
- API keys server-side only
- Input sanitization
- CORS configured for widget domains

## Support

For issues and questions:
1. Check the knowledge base
2. Review rules configuration
3. Verify API key setup
4. Check Render logs

## License

MIT License - Use freely for personal and commercial projects.