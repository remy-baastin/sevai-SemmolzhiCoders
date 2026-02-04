from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.services.rag_service import RAGService
from app.services.digilocker_service import DigiLockerService
from app.services.ocr_service import OCRService
from app.models import ChatRequest, UserProfile
import json

app = FastAPI()

# 1. Enable CORS (So Frontend can talk to Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Initialize Services
print("🚀 Starting Sev-ai Backend...")
rag_engine = RAGService()
digilocker = DigiLockerService()
ocr_engine = OCRService()
print("✅ Services Ready!")

# --- ROOT ---
@app.get("/")
def read_root():
    return {"message": "Sev-ai Backend is Running 🚀"}

# --- DIGILOCKER ROUTES ---
@app.get("/api/auth/url")
def get_auth_url():
    return {"url": digilocker.get_auth_url()}

@app.post("/api/auth/token")
def get_token(code: str):
    return digilocker.get_access_token(code)

@app.get("/api/user/profile")
def get_user_profile(token: str):
    return digilocker.get_user_details(token)

@app.get("/api/user/files")
def get_user_files(token: str):
    return digilocker.get_issued_documents(token)

# --- OCR ROUTE 1: AUTO-DETECT (The "Old Power") ---
@app.post("/api/extract-from-doc")
async def extract_from_doc(file: UploadFile = File(...)):
    """
    Standard Mode: Upload a file, and we guess if it's Aadhaar/Income/DL.
    """
    try:
        contents = await file.read()
        raw_text = ocr_engine.extract_text(contents)
        parsed_data = ocr_engine.parse_document(raw_text)
        return {"status": "success", "data": parsed_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- OCR ROUTE 2: AGENT MODE (The "New Power") ---
@app.post("/api/extract-custom")
async def extract_custom_field(
    file: UploadFile = File(...), 
    target_label: str = Form(...) 
):
    """
    Agent Mode: You tell us what to look for (e.g. 'Kisan ID').
    """
    try:
        contents = await file.read()
        raw_text = ocr_engine.extract_text(contents)
        result = ocr_engine.extract_dynamic_field(raw_text, target_label)
        return {
            "status": "success", 
            "search_result": result,
            "raw_text_snippet": raw_text[:100] 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- CHAT ROUTE (RAG) ---
@app.post("/api/recommend")
async def get_recommendations(request: ChatRequest):
    """
    The Brain Endpoint.
    Input: JSON Profile + Query + History
    Output: JSON Advice
    """
    try:
        json_response_str = rag_engine.recommend_schemes(
            request.user_profile, 
            request.query, 
            request.history
        )
        return json.loads(json_response_str)
    except Exception as e:
        return {
            "eligible": False, 
            "scheme_name": "Error", 
            "reason": "AI Processing Failed",
            "debug_error": str(e)
        }