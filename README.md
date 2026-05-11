# FitGuide — AI Fitness Trainer Chatbot

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Rishabh-Baloni/chat-bot)

A self-hosted onboarding and guidance assistant for the **AI Fitness Trainer** web app. FitGuide helps users figure out where to start, gives general fitness and nutrition guidance, and routes them to the right module (Exercise Library, Pose Detection, Meal Planner, Progress Analytics) with a concrete next action.

Built on Flask + Groq (LLM) with an embeddable JS widget. Deploys to Render free tier in one click.

## Features

- **One-file persona.** The full FitGuide system prompt lives in `rules/rules.txt`. Edit it and restart — no code change needed.
- **Module-aware routing.** FitGuide knows the AI Fitness Trainer modules and points users to specific routes (`/workout`, `/pose-detection`, `/diet`, `/analytics`).
- **Embeddable widget.** Drop one `<script>` tag into any page.
- **Built-in safety net.** Injuries, pregnancy, surgery recovery, disordered eating, and chronic illness automatically trigger a professional-referral notice — even if the LLM forgets.
- **Bounded memory.** Per-IP rate limit, per-session history cap, idle-session eviction. Safe to run on a single Render instance.
- **No new infra.** No Redis, no database. Stateless restart = fresh conversations.

## Quick start

### 1. Deploy to Render

1. Get a [Groq API key](https://console.groq.com/keys) (free tier is fine).
2. Fork this repo.
3. Click **Deploy to Render** above.
4. Set `GROK_API_KEY` in the Render environment.
5. Done. Your bot lives at `https://<your-app>.onrender.com`.

### 2. Embed the widget

```html
<script src="https://<your-app>.onrender.com/widget/widget.js"></script>
```

That's it. A chat button appears bottom-right of every page.

### 3. Local development

```bash
git clone https://github.com/Rishabh-Baloni/chat-bot
cd chat-bot
cp .env.example .env
# add your GROK_API_KEY to .env

pip install -r requirements.txt
cd app && python main.py
```

Then open `examples/demo.html` (after pointing `API_URL` at `http://localhost:8000`).

## Repository layout

```
app/
  main.py               # Flask server + FitGuide prompt assembly + safety net
  operational_safety.py # Referral-trigger helpers (also used by the optional FastAPI path)
  ...                   # Additional modules for an optional FastAPI variant
widget/
  widget.js             # Embeddable chat widget
  widget.css            # Widget styling
knowledge/
  core_knowledge.json   # Fitness knowledge base — keyword-matched and injected into prompts
rules/
  rules.txt             # FitGuide system prompt (single source of truth)
tests/
  test_loop.py          # End-to-end smoke test against a running server
examples/
  demo.html             # Local demo page
```

## API

- `POST /chat` — `{ "message": "...", "session_id": "..." }` → `{ "response": "...", "stage": "...", "session_id": "..." }`
- `GET /health` — service + config snapshot
- `GET /widget/widget.js` — embeddable widget

## Customization

### Change FitGuide's persona, tone, or knowledge of the app
Edit `rules/rules.txt`. Restart the server.

### Add app-specific facts (new modules, new diet types, etc.)
Append an entry to `knowledge/core_knowledge.json`:

```json
{
  "topic": "New module name",
  "keywords": ["keyword", "another keyword"],
  "response_guidance": "What you want FitGuide to say when these come up."
}
```

### Tighten or loosen safety limits
All knobs are in `.env.example` (rate limit, message length, history cap, allowed origins). Defaults are safe — set them only if you want to deviate.

### Restrict CORS to your real domain
```
ALLOWED_ORIGINS=https://your-fitness-app.com,https://www.your-fitness-app.com
```

### Style the widget
```html
<script>
  window.ChatbotConfig = {
    headerText: 'Coach',
    placeholder: 'Ask anything about your training...',
    theme: 'dark',
    position: 'bottom-left'
  };
</script>
<script src="https://<your-app>.onrender.com/widget/widget.js"></script>
```

## Safety model

FitGuide is **not a doctor, dietitian, or licensed professional**. The bot is configured to:

- Decline diagnosing injuries, illnesses, or medical conditions.
- Decline extreme calorie restrictions and prolonged fasting protocols.
- Decline supplement/PED advice beyond standard ones (with a "talk to your doctor" caveat).
- Auto-append a professional-referral notice whenever the user mentions an injury, pregnancy, surgery recovery, chronic illness, or disordered eating — regardless of what the model says.

Full safety policy lives in `rules/rules.txt` under "Hard boundaries".

## Cost

- **Render**: free tier (750 hours/month).
- **Groq**: ~$0.10 per 1M tokens. A casual deployment costs cents per month.

## License

MIT — use freely for personal and commercial projects.
