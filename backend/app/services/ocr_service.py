import pytesseract
from PIL import Image
import io
import re
import os

class OCRService:
    def __init__(self):
        # ---------------------------------------------------------
        # CRITICAL: Verify this path matches your Tesseract installation
        # ---------------------------------------------------------
        default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path
        else:
            print(f"WARNING: Tesseract not found at {default_path}. OCR will fail unless added to PATH.")

    def extract_text(self, file_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Extract text
            text = pytesseract.image_to_string(image, lang='eng') 
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def parse_document(self, text: str) -> dict:
        """
        Extracts Aadhaar/PAN data from raw text using Regex.
        """
        data = {
            "raw_text": text,
            "extracted_data": {}
        }
        
        clean_text = text.replace('\n', ' ')

        # 1. Aadhaar Regex (XXXX XXXX XXXX)
        aadhaar_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', clean_text)
        if aadhaar_match:
            data["extracted_data"]["aadhaar_number"] = aadhaar_match.group(0)

        # 2. PAN Card Regex (5 letters, 4 digits, 1 letter)
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', clean_text)
        if pan_match:
             data["extracted_data"]["pan_number"] = pan_match.group(0)

        return data