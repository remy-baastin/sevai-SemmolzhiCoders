from groq import Groq
import base64
import os
import json
import re
from dotenv import load_dotenv

class OCRLLMService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY") 
        if not api_key:
             print("❌ CRITICAL: GROQ_API_KEY missing.")
        
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def extract_text(self, file_bytes):
        base64_image = base64.b64encode(file_bytes).decode('utf-8')

        # --- UNIVERSAL PROMPT ---
        prompt = """
        Analyze this document image deeply. It could be ANY type of document (ID Card, Marks Sheet, Certificate, Bill, etc.).
        
        TASK:
        1. Identify the Document Type.
        2. Extract ALL visible text fields, labels, and values.
        3. If it contains a table (like marks), try to extract key rows.
        4. Standardize personal details if found (Name, DOB, Parents).

        OUTPUT JSON STRUCTURE:
        {
            "document_type": "string (e.g., Class XII Marks Statement)",
            "standardized_data": {
                "full_name": "string or null",
                "dob": "DD/MM/YYYY or null",
                "father_name": "string or null",
                "mother_name": "string or null",
                "id_number": "string (Roll No, Reg No, or ID No)",
                "mobile": "string or null",
                "email": "string or null",
                "address": "string or null"
            },
            "specific_data": {
                "school_name": "string",
                "board_name": "string",
                "year": "string",
                "subjects": ["Math", "Physics", ...],
                "result": "PASS/FAIL",
                ... (any other fields you see)
            }
        }
        
        Return ONLY valid JSON.
        """

        try:
            print("👁️ Sending Image to Universal Vision AI...")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": { # <--- FIXED HERE
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                        ],
                    }
                ],
                model=self.model,
                temperature=0,
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"❌ Vision LLM Error: {e}")
            return "{}"

    def parse_document(self, raw_json_str):
        try:
            # Clean JSON
            json_match = re.search(r'\{.*\}', raw_json_str, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = {}

            return {
                "status": "success",
                "document_type": data.get("document_type", "Unknown"),
                "extracted_data": data
            }

        except Exception as e:
            print(f"❌ Parsing Error: {e}")
            return {"status": "error", "error": str(e)}