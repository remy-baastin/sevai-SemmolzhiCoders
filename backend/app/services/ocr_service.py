import pytesseract
from PIL import Image
import io
import re

# Update this path for your system
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRService:
    def extract_text(self, file_bytes):
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # English is sufficient for standard Aadhaar
            text = pytesseract.image_to_string(image, lang='eng') 
            return text
        except Exception as e:
            print(f"❌ OCR Error: {e}")
            return ""

    def parse_document(self, text):
        """
        Extracts raw data and maps it to NSDL PAN Form fields.
        """
        data = {}
        text_lower = text.lower()
        
        # 1. Detect Doc Type
        if "unique identification" in text_lower or "aadhaar" in text_lower or "government of india" in text_lower:
             data["document_type"] = "Aadhaar Card"
        else:
             data["document_type"] = "Unknown"

        # 2. Extract Raw Details (Aadhaar Specific)
        if data["document_type"] == "Aadhaar Card":
            # A. Name (Look for "To" line common in letters, or English text blocks)
            # Regex: "To" followed by Name OR just a capitalized name line
            name_match = re.search(r"(?:To|To,)\s+([A-Z][a-zA-Z\s\.]+)", text)
            if name_match:
                data["raw_name"] = name_match.group(1).strip().replace("\n", " ")
            else:
                # Fallback: Look for the line above "DOB"
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if "dob" in line.lower() or "year of birth" in line.lower():
                        # The name is usually 1 or 2 lines above DOB
                        if i > 0 and len(lines[i-1].strip()) > 3:
                            data["raw_name"] = lines[i-1].strip()
                        elif i > 1:
                            data["raw_name"] = lines[i-2].strip()
                        break
            
            # B. Date of Birth (DD/MM/YYYY)
            dob_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
            if dob_match:
                data["dob"] = dob_match.group(1)
            
            # C. Gender (Male/Female)
            if "female" in text_lower:
                data["gender"] = "Female"
            elif "male" in text_lower:
                data["gender"] = "Male"
            else:
                data["gender"] = "Unknown"

            # D. UID (Aadhaar Number)
            uid_match = re.search(r"\d{4}\s\d{4}\s\d{4}", text)
            if uid_match:
                data["uid"] = uid_match.group(0)

        # 3. MAP TO PAN FORM FIELDS (The Requirement)
        pan_data = self.map_to_pan_form(data)

        return {
            "document_type": data.get("document_type", "Unknown"),
            "extracted_data": data,           # Raw extracted info
            "pan_form_data": pan_data,        # Form-ready JSON
            "raw_text_snippet": text[:200]
        }

    def map_to_pan_form(self, raw_data):
        """
        Converts raw data into NSDL Dropdown/Field values.
        """
        form = {
            # Default Fields
            "application_type": "New PAN - Indian Citizen (Form 49A)",
            "category": "INDIVIDUAL",
            
            # Personal Data
            "title": "---Please Select---",
            "last_name": "",
            "first_name": "",
            "middle_name": "",
            "dob": raw_data.get("dob", ""),
            
            # Missing Data (User must provide)
            "email": "",
            "mobile": ""
        }

        # Logic: Title based on Gender
        gender = raw_data.get("gender", "Unknown")
        if gender == "Male":
            form["title"] = "Shri"
        elif gender == "Female":
            form["title"] = "Smt" # Or Kumari, but Smt is safer default
        
        # Logic: Name Splitting
        # Input: "Remy Baastin Rayappan"
        # Output: First="Remy", Middle="Baastin", Last="Rayappan"
        raw_name = raw_data.get("raw_name", "")
        if raw_name:
            parts = raw_name.split()
            if len(parts) == 1:
                form["last_name"] = parts[0] # Surname is mandatory
            elif len(parts) == 2:
                form["first_name"] = parts[0]
                form["last_name"] = parts[1]
            else:
                form["first_name"] = parts[0]
                form["last_name"] = parts[-1]
                form["middle_name"] = " ".join(parts[1:-1])

        return form

    def extract_dynamic_field(self, text, target_label):
        pattern = re.compile(f"{re.escape(target_label)}[:\s\-]+(.*?)(?:\n|$)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
             return {"found": True, "label": target_label, "value": match.group(1).strip()}
        return {"found": False, "label": target_label}