import requests
import json

url = "http://127.0.0.1:8000/api/chat"

# SCENARIO: User replies with the missing email
payload = {
    "user_profile": {"name": "Remy Baastin Rayappan"},
    "query": "Okay, my email is remy.test@gmail.com and I want to apply for PAN.",
    "history": [
        "User: Apply for PAN",
        "AI: I need your email ID."
    ]
}

print("📤 Sending Reply: 'My email is remy03828@gmail.com'...")
try:
    response = requests.post(url, json=payload)
    data = response.json()
    
    print("\n--- 🤖 AI RESPONSE ---")
    print(f"💬 Text: {data.get('response_text')}")
    
    # This should now be "TRIGGER_RPA"
    print(f"⚡ Action Triggered: {data.get('action')}")
    
    if data.get("rpa_status"):
        print(f"\n🚀 RPA STATUS: {data['rpa_status']}")
        
except Exception as e:
    print(f"❌ Error: {e}")