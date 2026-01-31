# 🚀 Quick Setup Guide

## 1. Get API Keys

### Groq API Key (Required)
1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up/login
3. Create a new API key
4. Copy the key (starts with `gsk_`)

### Gemini API Key (Required)
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with Google account
3. Create API key
4. Copy the key (starts with `AIza`)

## 2. Deploy to Render

### Option A: One-Click Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Rishabh-Baloni/chat-bot)

### Option B: Manual Deploy
1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create new Web Service
4. Connect your forked repo
5. Set environment variables:
   - `GROK_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Gemini API key

## 3. Embed Widget

Add to any website:
```html
<script src="https://your-app-name.onrender.com/widget/widget.js"></script>
```

## 4. Test Your Bot

Create a test HTML file:
```html
<!DOCTYPE html>
<html>
<head><title>Test Bot</title></head>
<body>
    <h1>My Website</h1>
    <script src="https://your-app-name.onrender.com/widget/widget.js"></script>
</body>
</html>
```

## 5. Customize

- **Behavior**: Edit `rules/rules.txt`
- **Knowledge**: Edit `knowledge/core_knowledge.json`
- **Appearance**: Modify `widget/widget.css`

## Need Help?

Check the main [README.md](README.md) for detailed documentation.