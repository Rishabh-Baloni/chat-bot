from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import httpx
import uuid
import time
import re
import threading
from collections import defaultdict, deque
from dotenv import load_dotenv

# Robust path handling for .env loading
basedir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(basedir)
load_dotenv(dotenv_path=os.path.join(parent_dir, ".env"), override=False)
load_dotenv(dotenv_path=os.path.join(basedir, ".env"), override=False)

# Configuration
GROK_API_KEY = os.getenv("GROK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Tunable safety knobs (env-overridable, but ship with safe defaults so the app
# works on Render with zero additional configuration).
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
MAX_TURNS_PER_SESSION = int(os.getenv("MAX_TURNS_PER_SESSION", "20"))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "5000"))
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

# Paths to project-level resources (relative to this file)
RULES_PATH = os.path.join(parent_dir, "rules", "rules.txt")
KNOWLEDGE_PATH = os.path.join(parent_dir, "knowledge", "core_knowledge.json")

# Fallback used only if rules/rules.txt is missing or unreadable.
FALLBACK_SYSTEM_PROMPT = (
    "You are FitGuide, the friendly onboarding assistant inside the AI Fitness Trainer "
    "web app. Help users figure out where to start, give general fitness and nutrition "
    "guidance, and point them to specific app modules (Exercise Library, Pose Detection, "
    "Meal Planner, Progress Analytics). You are not a doctor or dietitian — refer medical "
    "questions to a qualified professional. Keep answers short and concrete."
)


def load_system_prompt() -> str:
    """Load the FitGuide system prompt from rules/rules.txt at startup."""
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content or FALLBACK_SYSTEM_PROMPT
    except Exception as e:
        print(f"Warning: failed to load rules.txt ({e}); using fallback prompt.")
        return FALLBACK_SYSTEM_PROMPT


SYSTEM_PROMPT = load_system_prompt()


# Boot-time configuration sanity check. We log loudly but do NOT crash so that
# /health stays reachable on a misconfigured deploy.
def _validate_env() -> None:
    missing = []
    if not GROK_API_KEY:
        missing.append("GROK_API_KEY")
    if missing:
        print(
            "WARNING: missing required env vars: "
            + ", ".join(missing)
            + ". /chat will return errors until they are set."
        )


_validate_env()


app = Flask(__name__)
_cors_origins = "*" if ALLOWED_ORIGINS.strip() == "*" else [
    o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()
]
CORS(app, resources={r"/*": {"origins": _cors_origins}})


# In-process state. This is intentionally simple — single-instance Render free
# tier means we don't need Redis, but we DO need bounded memory.
conversations: dict[str, list[str]] = {}
conversation_stages: dict[str, str] = {}
session_last_seen: dict[str, float] = {}
_state_lock = threading.Lock()

# Per-IP rate limit state.
_ip_hits: dict[str, deque] = defaultdict(deque)
_rate_lock = threading.Lock()


def _client_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _rate_limited(ip: str) -> bool:
    """Return True if this IP has exceeded the per-window request budget."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SEC
    with _rate_lock:
        hits = _ip_hits[ip]
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_MAX_REQUESTS:
            return True
        hits.append(now)
        # Opportunistic cleanup so the dict cannot grow without bound.
        if len(_ip_hits) > 10000:
            stale = [k for k, v in _ip_hits.items() if not v or v[-1] < cutoff]
            for k in stale[:1000]:
                _ip_hits.pop(k, None)
        return False


# Prompt-injection-ish patterns we'd rather not forward verbatim. This is a
# light defense, not a panacea — the LLM itself is told to ignore overrides
# in the system prompt.
_SUSPICIOUS_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror= ...
]


def _sanitize_input(raw: str) -> str:
    """Trim, length-cap, and strip control characters from user input."""
    if not raw or not isinstance(raw, str):
        return ""
    text = raw[:MAX_MESSAGE_LENGTH]
    # Strip ASCII control chars except newline (\n) and tab (\t).
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    return text.strip()


def _looks_suspicious(text: str) -> bool:
    return any(p.search(text) for p in _SUSPICIOUS_PATTERNS)


# Referral triggers — when present, we append a professional-referral notice to
# the bot's reply regardless of what the LLM said. Belt-and-braces safety net.
_REFERRAL_KEYWORDS = (
    "injured", "injury", "tore", "torn", "sprain", "sprained",
    "broken bone", "fracture", "fractured", "dislocated",
    "pregnant", "pregnancy", "postpartum",
    "surgery", "post-op", "recovering from surgery",
    "chronic illness", "diabetes", "heart condition",
    "disordered eating", "eating disorder", "anorexia", "bulimia",
)

_REFERRAL_NOTICE = (
    "\n\nHeads up: that sounds like it's better handled by a qualified "
    "professional (doctor, physical therapist, registered dietitian, or "
    "licensed mental health provider) than by a general fitness assistant. "
    "Please reach out to one — I'll be here to help you ease back in once "
    "you're cleared."
)


def _needs_referral_notice(message: str) -> bool:
    lo = message.lower()
    return any(kw in lo for kw in _REFERRAL_KEYWORDS)


def _evict_old_sessions(now: float) -> None:
    """Evict sessions that haven't been touched in SESSION_TTL_SECONDS, and
    trim to MAX_SESSIONS by oldest last_seen if still over budget."""
    cutoff = now - SESSION_TTL_SECONDS
    stale = [sid for sid, ts in session_last_seen.items() if ts < cutoff]
    for sid in stale:
        conversations.pop(sid, None)
        conversation_stages.pop(sid, None)
        session_last_seen.pop(sid, None)
    if len(session_last_seen) > MAX_SESSIONS:
        # Drop the oldest 10% to give ourselves headroom.
        sorted_sids = sorted(session_last_seen.items(), key=lambda kv: kv[1])
        drop = sorted_sids[: max(1, len(sorted_sids) // 10)]
        for sid, _ in drop:
            conversations.pop(sid, None)
            conversation_stages.pop(sid, None)
            session_last_seen.pop(sid, None)


@app.route('/')
def root():
    return {"message": "FitGuide chatbot engine running", "widget_url": "/widget/widget.js"}


@app.route('/health')
def health():
    return {
        "status": "healthy",
        "services": {
            "grok_api": bool(GROK_API_KEY),
            "gemini_api": bool(GEMINI_API_KEY),
        },
        "active_sessions": len(session_last_seen),
        "config": {
            "max_message_length": MAX_MESSAGE_LENGTH,
            "max_turns_per_session": MAX_TURNS_PER_SESSION,
            "rate_limit_per_minute": RATE_LIMIT_MAX_REQUESTS,
        },
    }


@app.route('/chat', methods=['POST'])
def chat():
    session_id = None
    try:
        data = request.get_json(silent=True) or {}
        raw_message = data.get('message', '')
        session_id = data.get('session_id') or str(uuid.uuid4())

        ip = _client_ip()
        if _rate_limited(ip):
            return jsonify({
                "response": "You're sending messages a little too fast. Please wait a few seconds and try again.",
                "session_id": session_id,
                "version": "1.0.0",
            }), 429

        message = _sanitize_input(raw_message)
        if not message:
            return jsonify({"error": "Message required"}), 400
        if _looks_suspicious(message):
            return jsonify({
                "response": "I can't process that type of message. Please try a different question.",
                "session_id": session_id,
                "version": "1.0.0",
            })

        now = time.time()
        with _state_lock:
            # Bootstrap session and prune stale state.
            if session_id not in conversations:
                conversations[session_id] = []
                conversation_stages[session_id] = "greeting"
            session_last_seen[session_id] = now
            _evict_old_sessions(now)

            current_stage = conversation_stages[session_id]
            conversations[session_id].append(f"User: {message}")

            # Cap per-session history so prompts stay bounded.
            max_msgs = MAX_TURNS_PER_SESSION * 2
            if len(conversations[session_id]) > max_msgs:
                conversations[session_id] = conversations[session_id][-max_msgs:]

            conversation_context = "\n".join(conversations[session_id])
            next_stage = determine_next_stage(current_stage, message)

            # Reset history when restarting from a goodbye state.
            if next_stage == "greeting" and current_stage == "goodbye":
                conversations[session_id] = [f"User: {message}"]
                conversation_context = f"User: {message}"

            conversation_stages[session_id] = next_stage

        response_text = call_groq_api(message, conversation_context, next_stage)

        if _needs_referral_notice(message) and "qualified professional" not in response_text.lower():
            response_text = response_text + _REFERRAL_NOTICE

        with _state_lock:
            # Append bot response to history (and re-cap, since we just added a line).
            history = conversations.get(session_id)
            if history is not None:
                history.append(f"Assistant: {response_text}")
                max_msgs = MAX_TURNS_PER_SESSION * 2
                if len(history) > max_msgs:
                    conversations[session_id] = history[-max_msgs:]

        debug_info = {
            "current_stage": current_stage,
            "next_stage": next_stage,
        } if os.getenv("DEBUG") else None

        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "version": "1.0.0",
            "stage": next_stage,
            "debug": debug_info,
        })

    except Exception as e:
        print(f"Chat Endpoint Error: {str(e)}")
        return jsonify({
            "response": "I'm having a hiccup on my end. Please try again in a moment.",
            "session_id": session_id,
            "version": "1.0.0",
        }), 500


# Words that mean "I'm starting fresh / saying hi"
RESTART_KEYWORDS = {"hi", "hello", "hey", "start over", "restart", "new chat", "greetings"}

# Words that mean "I'm done with this conversation". Intentionally NOT
# including "thanks"/"thank you" — those are mid-conversation politeness, not
# session terminators.
GOODBYE_KEYWORDS = {"bye", "goodbye", "that's all", "see ya", "see you", "later"}


def determine_next_stage(current_stage: str, message: str) -> str:
    """Simple flow: greeting -> chatting -> goodbye, with restart support."""
    message_lower = message.lower().strip().strip('.,!?')

    # After a goodbye, any further message restarts the conversation.
    # A bare "hi/hello" reopens as greeting; anything substantive goes straight
    # to chatting so we don't drag the user through a fake greeting first.
    if current_stage == "goodbye":
        first_word = message_lower.split()[0] if message_lower else ""
        if message_lower in RESTART_KEYWORDS or first_word in RESTART_KEYWORDS:
            return "greeting"
        return "chatting"

    if current_stage in {"greeting", "chatting"}:
        if any(kw in message_lower for kw in GOODBYE_KEYWORDS):
            return "goodbye"

    if current_stage == "greeting":
        return "chatting"
    return "chatting"


def find_relevant_knowledge(message: str) -> str:
    """Return the first matching knowledge entry's guidance as an extra hint."""
    try:
        with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        message_lower = message.lower()
        for entry in knowledge_data:
            keywords = entry.get('keywords', [])
            if any(str(kw).lower() in message_lower for kw in keywords):
                return entry.get('response_guidance', '')
    except Exception:
        pass
    return ""


def _windowed_context(context: str, max_msgs: int = 8) -> str:
    """Trim the joined conversation context to the most recent N messages.

    The full per-session history is preserved in memory; we only send the last
    few turns to the model to keep token usage bounded.
    """
    if not context:
        return ""
    lines = context.split("\n")
    return "\n".join(lines[-max_msgs:])


def call_groq_api(message: str, conversation_context: str = "", next_stage: str = "chatting") -> str:
    if not GROK_API_KEY:
        return (
            "FitGuide is not fully configured yet — the server is missing its API key. "
            "If you're the operator, set GROK_API_KEY in your environment."
        )
    try:
        relevant_knowledge = find_relevant_knowledge(message)
        windowed = _windowed_context(conversation_context, max_msgs=8)

        system_prompt_parts = [SYSTEM_PROMPT]

        if windowed:
            system_prompt_parts.append(
                "Conversation so far (most recent at the bottom):\n" + windowed
            )

        if relevant_knowledge:
            system_prompt_parts.append(
                "Relevant app context for this question:\n" + relevant_knowledge
            )

        if next_stage == "goodbye":
            system_prompt_parts.append(
                "The user is wrapping up. Give a short, warm sign-off (1-2 sentences) and "
                "encourage them to come back when they want to keep going."
            )
        elif next_stage == "greeting":
            system_prompt_parts.append(
                "This is the start of the conversation. Greet the user briefly and either "
                "answer their question or ask one short clarifying question to point them "
                "to the right module."
            )

        # Final terse-output reinforcement — small models like llama-3.1-8b
        # follow length constraints better when reminded immediately before
        # the user message.
        system_prompt_parts.append(
            "Reply in 2-4 sentences. No headings. No emoji. Plain prose."
        )

        system_prompt = "\n\n".join(system_prompt_parts)

        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "model": "llama-3.1-8b-instant",
            "temperature": 0.7,
            "max_tokens": 350,
        }
        url = "https://api.groq.com/openai/v1/chat/completions"

        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30)

            # Single retry on Groq rate-limit. The free tier resets quickly;
            # a short backoff is usually enough to recover transparently.
            if response.status_code == 429:
                time.sleep(1.5)
                response = client.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return "I received an empty response. Please try again."
            if response.status_code == 401:
                return "API authentication failed. Please check the API key."
            if response.status_code == 429:
                return (
                    "The AI service is rate-limited right now. Give it about 30 "
                    "seconds and try again."
                )
            print(f"Groq API non-200: {response.status_code} body={response.text[:300]}")
            return f"API returned status {response.status_code}. Please try again."

    except httpx.TimeoutException:
        return "Request timed out. Please try again."
    except Exception as e:
        print(f"Groq API Error: {str(e)}")
        return "Sorry, I hit a technical error. Please try again in a moment."


@app.route('/widget/<path:filename>')
def serve_widget(filename):
    return send_from_directory('../widget', filename)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
