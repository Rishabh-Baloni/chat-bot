"""Smoke test for the FitGuide chat endpoint.

Run the server first (`cd app && python main.py`) and then run this script.
It walks through a normal greeting -> chatting -> goodbye flow, then verifies
that a restart greeting resets the session.
"""

import json
import sys
import urllib.error
import urllib.request
import uuid

API_URL = "http://localhost:8000/chat"


def send_chat(message: str, session_id: str) -> dict:
    payload = json.dumps({"message": message, "session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Network error: {e}")
        return {"stage": "error", "response": str(e)}
    except Exception as e:
        print(f"Error: {e}")
        return {"stage": "error", "response": str(e)}


def assert_stage(resp: dict, expected: str, label: str) -> bool:
    actual = resp.get("stage")
    if actual != expected:
        print(f"FAIL [{label}]: expected stage={expected}, got stage={actual}")
        return False
    print(f"PASS [{label}]: stage={actual}")
    return True


def main() -> int:
    session_id = str(uuid.uuid4())
    print(f"Session: {session_id}\n")

    failures = 0

    # 1. Greeting -> bot should move to chatting after the first turn.
    resp = send_chat("hello", session_id)
    failures += 0 if assert_stage(resp, "chatting", "greeting transitions to chatting") else 1

    # 2. Normal fitness question -> stays in chatting.
    resp = send_chat("I want to lose weight, where do I start?", session_id)
    failures += 0 if assert_stage(resp, "chatting", "fitness question stays in chatting") else 1

    # 3. Follow-up question -> still chatting (no rigid funnel).
    resp = send_chat("I have no equipment at home.", session_id)
    failures += 0 if assert_stage(resp, "chatting", "follow-up stays in chatting") else 1

    # 4. Goodbye keyword -> moves to goodbye.
    resp = send_chat("thanks!", session_id)
    failures += 0 if assert_stage(resp, "goodbye", "thanks triggers goodbye") else 1

    # 5. Greeting after goodbye -> restarts to greeting.
    resp = send_chat("hi", session_id)
    failures += 0 if assert_stage(resp, "greeting", "hi after goodbye restarts to greeting") else 1

    # 6. Referral trigger -> response should include a referral notice.
    referral_session = str(uuid.uuid4())
    send_chat("hello", referral_session)
    resp = send_chat("I think I tore something in my knee", referral_session)
    body = (resp.get("response") or "").lower()
    if "qualified professional" in body or "physical therapist" in body or "doctor" in body:
        print("PASS [injury triggers referral language]")
    else:
        print(f"FAIL [injury triggers referral language]: response={body[:200]}")
        failures += 1

    print(f"\n{failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
