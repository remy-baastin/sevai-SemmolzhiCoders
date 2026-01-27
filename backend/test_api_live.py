import requests
import json

# 1. The URL of your new Local API
url = "http://localhost:8000/api/recommend"

# 2. The Data your Frontend will eventually send
payload = {
    "user_xml": """
    <User>
        <Name>Rahul Kumar</Name>
        <Age>19</Age>
        <Gender>Male</Gender>
        <Occupation>Student</Occupation>
        <Caste>SC</Caste>
        <Income>150000</Income>
        <Education>Class 12 Pass</Education>
    </User>
    """,
    "query": "I need financial help for university."
}

print("🚀 Sending request to Sev-ai API...")

try:
    # 3. Send the POST request
    response = requests.post(url, json=payload)
    
    # 4. Print the result
    if response.status_code == 200:
        print("\n✅ API RESPONSE (Success!):")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ API Error {response.status_code}:")
        print(response.text)

except Exception as e:
    print(f"\n❌ Connection Failed: {e}")
    print("Make sure 'uvicorn main:app' is running in the other terminal!")