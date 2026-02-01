import urllib.request
import json
import uuid
import sys

def send_chat(message, session_id):
    url = "http://localhost:10000/chat"
    data = {"message": message, "session_id": session_id}
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")
        return {"stage": "error", "response": str(e)}

def test_loop_bug():
    session_id = str(uuid.uuid4())
    print(f"Starting Session: {session_id}")
    
    # 1. Start Chat
    resp = send_chat("hello", session_id)
    print(f"1. Greeting: {resp['stage']}")
    
    # 2-6. Spam messages to increase count to >= 5
    for i in range(5):
        resp = send_chat(f"symptom {i}", session_id)
        print(f"Msg {i+2}. Stage: {resp['stage']}")
        
    # Now we should be in 'conclusion' (or close to it) because of count >= 5
    # Let's force conclusion if not there
    if resp['stage'] != "conclusion":
        resp = send_chat("treatment", session_id)
        print(f"Forced Conclusion. Stage: {resp['stage']}")
        
    # Now we are in conclusion.
    # Try saying "ok"
    print("--- Testing 'ok' loop ---")
    resp = send_chat("ok", session_id)
    print(f"Response to 'ok': Stage={resp['stage']}")
    
    if resp['stage'] == "conclusion":
        print("FAIL: Stuck in conclusion loop on 'ok'")
    else:
        print(f"SUCCESS: 'ok' led to {resp['stage']}")

    # Try saying "thank you" (if we didn't exit already, or restart session)
    # Let's restart session to test 'thank you' specifically
    session_id = str(uuid.uuid4())
    print(f"\nStarting Session 2: {session_id}")
    send_chat("hello", session_id)
    for i in range(5):
        send_chat(f"symptom {i}", session_id)
    send_chat("treatment", session_id) # Ensure conclusion
    
    print("--- Testing 'thank you' loop ---")
    resp = send_chat("thank you", session_id)
    print(f"Response to 'thank you': Stage={resp['stage']}")
    
    if resp['stage'] == "conclusion":
        print("FAIL: Stuck in conclusion loop on 'thank you'")
    else:
        print(f"SUCCESS: 'thank you' led to {resp['stage']}")

if __name__ == "__main__":
    test_loop_bug()
