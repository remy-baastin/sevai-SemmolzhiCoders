from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import json

# Services
from app.services.rag_service import RAGService
from app.services.data_service import DataService
from app.services.rpa_service import RPAService

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

print("⚡ Initializing Services...")
data_store = DataService()
rag_engine = RAGService()
rpa_engine = RPAService()
print("✅ Services Ready!")

class UserProfile(BaseModel):
    name: str

class SchemeRequest(BaseModel):
    user_profile: UserProfile
    query: str
    history: List[str] = []

@app.post("/api/chat")
async def chat_endpoint(request: SchemeRequest):
    try:
        # 1. Ask Brain
        response_json_str = rag_engine.recommend_schemes(request.user_profile, request.query, request.history)
        try:
            ai_response = json.loads(response_json_str)
        except:
            return {"response_text": response_json_str, "action": "NONE"}

        user_name = request.user_profile.name

        # 2. Self-Healing (Update DB with new info)
        extracted = ai_response.get("extracted_data")
        if extracted and isinstance(extracted, dict):
            print(f"📥 New Data Detected: {extracted}")
            update_payload = {"standardized_data": extracted}
            data_store.update_user_data(user_name, update_payload)

        # 3. CHECK FOR ACTION
        if ai_response.get("action") == "TRIGGER_RPA":
            target_scheme = ai_response.get("target_scheme", "Unknown Scheme")
            
            # Fetch fresh data
            full_user_data = data_store.get_user_data(user_name)
            
            # --- FIXED EXTRACTION LOGIC ---
            profile_root = full_user_data.get("profile", {})
            
            # Check if names are nested inside 'personal_details' (Common in OCR data)
            personal_info = profile_root.get("personal_details", profile_root)
            
            # Check if contact is nested inside 'contact_details'
            contact_info = profile_root.get("contact_details", profile_root)

            # Get Docs (for Marks)
            docs = full_user_data.get("documents", [])
            marks_data = {}
            for doc in docs:
                if doc.get("type") == "Marks Sheet":
                    marks_data = doc.get("data", {})

            # Construct Payload with CORRECT Paths
            rpa_data = {
                "personal_details": {
                    "first_name": personal_info.get("first_name", ""),
                    "middle_name": personal_info.get("middle_name", ""),
                    "last_name": personal_info.get("last_name", ""), # Now correctly fetches "Rayappan"
                    "dob": personal_info.get("dob", ""),
                    "father_name": marks_data.get("Father Name") or personal_info.get("father_name", "")
                },
                "contact_details": {
                    "mobile": contact_info.get("mobile", profile_root.get("mobile", "")),
                    "email": contact_info.get("email", profile_root.get("email", ""))
                },
                "education_details": {
                    "board": marks_data.get("Board", "State Board"),
                    "marks": {"physics": marks_data.get("Physics"), "total": marks_data.get("Total")}
                }
            }
            
            print(f"🚀 Launching RPA for {target_scheme}...")
            # Debug Print to confirm it worked
            print(f"   Name extracted: {rpa_data['personal_details']['first_name']} {rpa_data['personal_details']['last_name']}")
            
            rpa_result = rpa_engine.apply_for_scheme(rpa_data, scheme_name=target_scheme)
            
            ai_response["response_text"] += f"\n\n🚀 [System]: Application process started! {rpa_result.get('message', '')}"
            ai_response["rpa_status"] = rpa_result

        return ai_response

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))