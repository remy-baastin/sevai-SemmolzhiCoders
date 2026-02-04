from app.services.rag_service import RAGService
import time
import json

# Mock class to simulate the FastAPI User Profile object
class MockUserProfile:
    def __init__(self, name):
        self.name = name

def test_brain():
    print("🚀 Initializing Sev-ai Brain...")
    rag = RAGService()
    
    # 1. Define the User (Must match a name in your user_db.json)
    # We use the name from your Marks Sheet upload earlier
    user_name = "Remy Baastin Rayappan" 
    mock_user = MockUserProfile(user_name)
    
    # 2. Define the Query
    # A complex query that requires knowing Scheme Data + User Marks
    query = "I am a student with good marks in Physics. Are there any scholarships for me?"
    
    print(f"\n👤 Testing for User: {user_name}")
    print(f"❓ Query: {query}")
    print("\n--- 🧠 THINKING (Connecting Memory + Database) ---")
    
    start_time = time.time()
    
    # 3. Get Recommendation
    # passing [] as history for now
    response_json = rag.recommend_schemes(mock_user, query, [])
    
    end_time = time.time()
    
    # 4. Parse & Display
    try:
        data = json.loads(response_json)
        print("\n--- ✅ AI RESPONSE ---")
        print(f"💬 Summary: {data.get('response_text')}")
        print(f"\n🏆 Eligible Schemes: {data.get('eligible_schemes')}")
        print(f"⚠️ Potential Schemes: {data.get('potential_schemes')}")
        print(f"🔍 Missing Data: {data.get('missing_data_for_application')}")
    except:
        print("\n--- ⚠️ RAW RESPONSE (JSON Parse Failed) ---")
        print(response_json)

    print(f"\n⏱️ Time Taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    test_brain()