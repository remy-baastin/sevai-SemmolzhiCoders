from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import OCRService
from app.services.digilocker_service import DigiLockerService

router = APIRouter()
ocr_service = OCRService()
digilocker_service = DigiLockerService()

# --- OCR ENDPOINTS (Manual Upload) ---
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Only JPEG or PNG images allowed")

    content = await file.read()
    text = ocr_service.extract_text(content)
    
    if not text:
        return {"status": "failed", "message": "No text extracted."}

    parsed_data = ocr_service.parse_document(text)
    return {"status": "success", "filename": file.filename, "data": parsed_data}

# --- DIGILOCKER ENDPOINTS (Verified Data) ---

@router.get("/digilocker/init")
def digilocker_init():
    """
    Step 1: Get the URL to redirect the user to (The 'Sign In' page).
    """
    url = digilocker_service.get_auth_url()
    return {"redirect_url": url}

@router.get("/digilocker/callback")
def digilocker_callback(code: str, state: str):
    """
    Step 2: The frontend sends the 'code' here to exchange for an Access Token.
    """
    # 1. Exchange Code for Token
    token_data = digilocker_service.get_access_token(code)
    if "error" in token_data:
        raise HTTPException(status_code=400, detail="Invalid Auth Code")
    
    # 2. Immediately fetch User Profile to confirm identity
    access_token = token_data["access_token"]
    user_profile = digilocker_service.get_user_details(access_token)
    
    return {
        "status": "success",
        "token": access_token, 
        "user": user_profile
    }

@router.get("/digilocker/documents")
def get_documents(token: str):
    """
    Step 3: Fetch list of issued documents (Marksheets, Aadhaar, etc.)
    """
    docs = digilocker_service.get_issued_documents(token)
    return docs

@router.get("/digilocker/xml")
def get_document_xml(uri: str, token: str):
    """
    Step 4: Fetch the MACHINE-READABLE XML for a specific document.
    This is what the Automation Engine (Module C) will read.
    """
    xml_data = digilocker_service.get_file_xml(uri, token)
    return {"uri": uri, "xml_content": xml_data}