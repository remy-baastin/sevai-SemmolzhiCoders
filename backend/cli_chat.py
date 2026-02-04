import requests
import json
import time

URL = "http://127.0.0.1:8000/api/chat"
USER_NAME = "Remy Baastin Rayappan"

def chat_session():
    print(f"🤖 Connected to Sev-ai as {USER_NAME}")
    print("Type 'exit' to quit.\n")

    # Start with empty history
    history = []

    while True:
        # 1. Get User Input
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # 2. Prepare Payload
        payload = {
            "user_profile": {"name": USER_NAME},
            "query": user_input,
            "history": history
        }

        # 3. Send to Backend
        try:
            print("Thinking...", end="\r")
            response = requests.post(URL, json=payload)
            data = response.json()

            # 4. Display Response
            bot_text = data.get("response_text", "No response text")
            print(f"🤖 Sev-ai: {bot_text}")

            # 5. Update History (So the bot remembers context!)
            history.append(f"User: {user_input}")
            history.append(f"AI: {bot_text}")

            # 6. Check for ACTION (The Magic Moment)
            if data.get("action") == "TRIGGER_RPA":
                print("\n🚀 SYSTEM: AUTOMATION TRIGGERED!")
                print(f"   Target: {data.get('target_scheme')}")
                rpa_res = data.get("rpa_status", {})
                print(f"   Status: {rpa_res.get('message')}")
                print("   (Check your other window for Chrome!)")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    chat_session()