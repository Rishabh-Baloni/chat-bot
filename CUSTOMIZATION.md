# 🎨 Customization Guide

## Bot Personality & Behavior

### Edit Rules (`rules/rules.txt`)
```txt
You are a helpful customer support assistant for [YOUR COMPANY].

Key behaviors:
- Always be polite and professional
- Respond in [YOUR LANGUAGE]
- Focus on [YOUR BUSINESS DOMAIN]
- If you don't know something, say "Let me connect you with a human agent"

Never:
- Give medical or legal advice
- Share personal information
- Make promises about pricing or availability
```

## Knowledge Base

### Core Knowledge (`knowledge/core_knowledge.json`)
Add your business-specific information:
```json
{
  "topic": "Business Hours",
  "symptoms_or_keywords": ["hours", "open", "closed", "schedule"],
  "response_guidance": "We're open Monday-Friday 9AM-6PM EST. Weekend support available via email.",
  "risk_level": "low",
  "confidence": 1.0,
  "source": "company_info"
}
```

### Auto-Expand Knowledge
Use the API to add knowledge from documents:
```bash
curl -X POST https://your-app.onrender.com/expand-knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Your company documentation text here...",
    "source_tag": "company_docs"
  }'
```

## Widget Appearance

### Basic Styling (`widget/widget.css`)
```css
/* Change colors */
.chat-button {
  background: #your-brand-color !important;
}

.chat-header {
  background: #your-brand-color !important;
}

/* Change position */
#chatbot-widget.bottom-left {
  bottom: 20px;
  left: 20px;
}
```

### Widget Configuration
```html
<script>
window.ChatbotConfig = {
  buttonText: '💬 Help',
  headerText: 'Your Company Support',
  placeholder: 'Ask us anything...',
  position: 'bottom-right', // bottom-left, top-right, top-left
  theme: 'default' // default, dark, light
};
</script>
<script src="https://your-app.onrender.com/widget/widget.js"></script>
```

## Advanced Customization

### Custom System Prompt
Edit `app/main.py` line with system prompt:
```python
"content": "You are a helpful assistant for [YOUR COMPANY]. [YOUR CUSTOM INSTRUCTIONS]"
```

### API Integration
```javascript
// Direct API usage
const response = await fetch('https://your-app.onrender.com/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello!',
    session_id: 'optional-session-id'
  })
});
```

### Multiple Widgets
Deploy multiple instances for different purposes:
- Customer support bot
- Sales assistant bot  
- Technical help bot

Each with different rules and knowledge bases.

## Examples

### E-commerce Bot
```txt
You are a shopping assistant for [STORE NAME].
Help customers find products, check order status, and handle returns.
Always ask for order numbers when discussing specific orders.
```

### SaaS Support Bot
```txt
You are a technical support assistant for [PRODUCT NAME].
Help users with account issues, feature questions, and troubleshooting.
Escalate billing questions to human agents.
```

### Restaurant Bot
```txt
You are a friendly assistant for [RESTAURANT NAME].
Help with reservations, menu questions, and dietary restrictions.
Our specialties are [LIST SPECIALTIES].
```