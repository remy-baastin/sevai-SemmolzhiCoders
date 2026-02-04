import pytesseract
from PIL import Image
import io
import re
import os

class OCRService:
    def __init__(self):
        # ---------------------------------------------------------
        # 🔧 CONFIGURATION
        # If on Windows, ensure this points to your installation.
        # If on Linux/Mac (Docker), this is usually auto-detected.
        # ---------------------------------------------------------
        default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path
        else:
            # We don't crash here because on some systems it's in PATH
            print(f"ℹ️ Note: Tesseract exe not found at {default_path}. Assuming it is in system PATH.")

    def extract_text(self, file_bytes: bytes) -> str:
        """
        Converts Image Bytes -> Raw Text
        """
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # 'eng' is standard. For Hindi support, you'd add 'hin' here later.
            text = pytesseract.image_to_string(image, lang='eng') 
            return text
        except Exception as e:
            print(f"❌ OCR Extraction Error: {e}")
            return ""

    def parse_document(self, text: str) -> dict:
        """
        The Brain of the OCR.
        1. Classifies the document (Aadhaar vs Income vs DL).
        2. Extracts specific fields based on the type.
        """
        
        # Normalize text for easier matching
        clean_text = text.replace('\n', ' ').strip()
        lower_text = clean_text.lower()

        response = {
            "document_type": "Unknown",
            "confidence": "Low",
            "extracted_data": {},
            "raw_text_snippet": clean_text[:100] + "..." # First 100 chars for debug
        }

        # =========================================================
        # 🕵️‍♂️ CLASSIFICATION LOGIC
        # =========================================================

        # --- 1. AADHAAR CARD ---
        if "uidai" in lower_text or "aadhaar" in lower_text or "govt of india" in lower_text:
            response["document_type"] = "Aadhaar Card"
            response["confidence"] = "High"
            
            # Regex: Finds 12 digits (XXXX XXXX XXXX)
            uid_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', clean_text)
            if uid_match:
                response["extracted_data"]["uid"] = uid_match.group(0)

            # Regex: Finds Date of Birth (DOB: DD/MM/YYYY)
            dob_match = re.search(r'DOB\s*:?\s*(\d{2}/\d{2}/\d{4})', clean_text, re.IGNORECASE)
            if dob_match:
                response["extracted_data"]["dob"] = dob_match.group(1)

        # --- 2. INCOME CERTIFICATE ---
        elif "income" in lower_text and ("certificate" in lower_text or "annual" in lower_text):
            response["document_type"] = "Income Certificate"
            response["confidence"] = "High"

            # Regex: Finds money amounts (Rs. 50,000 or 1,50,000) near the word "Income"
            # Looks for digits allowing for commas
            income_match = re.search(r'Income.*?(?:Rs\.?|INR)\s*([\d,]+)', clean_text, re.IGNORECASE)
            if income_match:
                raw_amount = income_match.group(1).replace(',', '')
                response["extracted_data"]["annual_income"] = int(raw_amount)

        # --- 3. CASTE / COMMUNITY CERTIFICATE ---
        elif "caste" in lower_text or "community" in lower_text or "backward" in lower_text:
            response["document_type"] = "Community Certificate"
            response["confidence"] = "High"

            if "sc" in lower_text or "scheduled caste" in lower_text:
                response["extracted_data"]["caste_category"] = "SC"
            elif "st" in lower_text or "scheduled tribe" in lower_text:
                response["extracted_data"]["caste_category"] = "ST"
            elif "obc" in lower_text:
                response["extracted_data"]["caste_category"] = "OBC"
            else:
                response["extracted_data"]["caste_category"] = "General"

        # --- 4. DRIVING LICENCE ---
        elif "driving" in lower_text and "licence" in lower_text:
            response["document_type"] = "Driving Licence"
            response["confidence"] = "High"
            
            # Regex: Standard Indian DL format (e.g., TN01 20200000123)
            # 2 chars + 2 digits + space(opt) + 11 digits (approx pattern)
            dl_match = re.search(r'[A-Z]{2}[0-9]{2}\s?[0-9]{4,13}', clean_text)
            if dl_match:
                response["extracted_data"]["dl_number"] = dl_match.group(0)

        # --- 5. PAN CARD ---
        elif "permanent account number" in lower_text or "income tax department" in lower_text:
             response["document_type"] = "PAN Card"
             response["confidence"] = "High"
             
             # Regex: 5 letters, 4 numbers, 1 letter
             pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', clean_text)
             if pan_match:
                 response["extracted_data"]["pan_number"] = pan_match.group(0)

        return response
    
    # ... (Keep existing __init__, extract_text, and parse_document) ...

    def extract_dynamic_field(self, text: str, target_label: str) -> dict:
        """
        SMART EXTRACTOR: 
        - If looking for an ID (Roll No, Income), it takes the first word.
        - If looking for a Name (School, Father), it takes the full phrase.
        """
        response = {
            "found": False,
            "label": target_label,
            "value": None,
            "confidence": "Low"
        }

        clean_text = text.replace('\n', '  ').strip()
        
        # 1. Regex: Capture everything after the label until double-space
        pattern = rf"{re.escape(target_label)}[:\-\s\.]*(.*?)(?:\s{2,}|\n|$)"
        match = re.search(pattern, clean_text, re.IGNORECASE)
        
        if match:
            raw_value = match.group(1).strip()
            clean_value = raw_value.lstrip(":,.- ") # Remove leading punctuation

            # 2. DECIDE: Is this a "Single Word ID" or a "Multi-Word Name"?
            # Check if label contains keywords like "No", "ID", "Code", "Income", "Date"
            id_keywords = ["no", "id", "num", "code", "date", "income", "uid", "dob", "roll", "reg", "marks"]
            is_id_field = any(k in target_label.lower() for k in id_keywords)

            if is_id_field:
                # --- MODE A: AGGRESSIVE (For IDs) ---
                # Take only the first word (e.g., "20670312 Mother..." -> "20670312")
                final_value = clean_value.split()[0]
            
            else:
                # --- MODE B: RELAXED (For Names/Schools) ---
                # Take the whole phrase, but stop if we hit a "Stop Word" (like the next field's name)
                # This prevents "School Name Mother Name" error.
                final_value = clean_value
                
                # Common labels that appear next to names
                next_field_stoppers = ["mother", "father", "parent", "class", "roll", "reg", "date", "addr", "exam"]
                
                lower_val = final_value.lower()
                for stop_word in next_field_stoppers:
                    # If we find " Mother" inside the value, cut it off there
                    idx = lower_val.find(f" {stop_word}") 
                    if idx != -1:
                        final_value = final_value[:idx].strip()
                        break

            # 3. Final Check: Ignore generic header words if caught by mistake
            if final_value.upper() not in ["CERTIFICATE", "MARK SHEET", "EXAMINATION", "OF"]:
                response["found"] = True
                response["value"] = final_value
                response["confidence"] = "High"
        
        return response