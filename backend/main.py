from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json

# Import your services
from app.services.digilocker_service import DigiLockerService
from app.services.rag_service import RAGService

app = FastAPI()

# 1. Enable CORS (So your React Frontend can talk to this Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (good for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Initialize Services (Load them once at startup)
# This prevents reloading the AI model on every request
print("🚀 Starting Sev-ai Backend...")
digilocker = DigiLockerService()
rag_engine = RAGService()
print("✅ Services Ready!")

# --- Data Models ---
class RAGRequest(BaseModel):
    user_xml: str
    query: str

# --- Routes ---

@app.get("/")
def read_root():
    return {"message": "Sev-ai Backend is Running 🚀"}

@app.get("/auth/url")
def get_digilocker_url():
    """Generates the URL to redirect user to DigiLocker"""
    return {"url": digilocker.get_auth_url()}

@app.get("/auth/callback")
def digilocker_callback(code: str, state: str):
    """Handles the return from DigiLocker"""
    token_data = digilocker.get_access_token(code)
    # In a real app, you would fetch the XML here using the token
    # For now, we return the token
    return token_data

@app.post("/api/recommend")
async def get_recommendations(request: RAGRequest):
    """
    The Brain Endpoint:
    Input: User XML + Question
    Output: Smart Scheme Advice
    """
    try:
        # Call the RAG Service
        json_response_str = rag_engine.recommend_schemes(request.user_xml, request.query)
        
        # Ensure we return actual JSON object, not a string
        return json.loads(json_response_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)