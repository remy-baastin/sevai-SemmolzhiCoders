import json
import uuid
import time
import os
from dotenv import load_dotenv
import requests
import base64

load_dotenv()

class DigiLockerService:
    def __init__(self):
        # Configuration
        self.client_id = os.getenv("DIGILOCKER_CLIENT_ID")
        self.client_secret = os.getenv("DIGILOCKER_CLIENT_SECRET")
        self.redirect_uri = "http://localhost:5173/callback" 
        self.base_url = "https://sandbox.api-setu.in/digilocker"
        
        # --- THE LOCAL "SANDBOX" DATA ---
        # This matches the JSON structure from API Setu / Your PDF Page 8 & 16
        self.mock_user = {
            "name": "Remy Baastin Rayappan",
            "dob": "31072005", # DDMMYYYY format as per Spec
            "gender": "M",
            "eaadhaar": "Y",
            "digilockerid": "36f1c4-mock-user-id-8821",
            "access_token": "mock_access_token_123",
            "scope": "files.issueddocs files.uploadeddocs",
        }

        self.mock_documents = {
            "items": [
                {
                    "name": "Class XII Marksheet",
                    "type": "file",
                    "size": "",
                    "date": "2023-05-12T10:00:00",
                    "parent": "",
                    "mime": ["application/pdf", "application/xml"], # XML is crucial for us
                    "uri": "in.gov.tn.dge-HSCM-120863261",
                    "doctype": "HSCM",
                    "description": "Class XII Marksheet",
                    "issuerid": "in.gov.tn.dge",
                    "issuer": "Tamil Nadu Board of Higher Secondary Education"
                },
                {
                    "name": "Aadhaar Card",
                    "type": "file",
                    "mime": ["application/pdf", "application/xml"],
                    "uri": "in.gov.uidai-ADHAR-581604284506",
                    "doctype": "ADHAR",
                    "description": "Aadhaar Card",
                    "issuer": "UIDAI"
                }
            ]
        }

    def get_auth_url(self):
        """
        Generates the detailed OAuth2 URL described in Spec Page 5.
        """
        state = uuid.uuid4().hex
        # In real life, this redirects to api.digitallocker.gov.in
        # For our demo, we redirect to our own frontend callback
        return f"http://localhost:5173/digilocker-callback?code=mock_auth_code&state={state}"

    def get_access_token(self, code: str):
        """
        Simulates the POST /oauth2/1/token call (Spec Page 6).
        """
        if code == "mock_auth_code":
            return {
                "access_token": self.mock_user["access_token"],
                "expires_in": 3600,
                "token_type": "Bearer",
                "digilockerid": self.mock_user["digilockerid"]
            }
        return {"error": "invalid_grant"}

    def get_user_details(self, token: str):
        """
        Simulates GET /oauth2/1/user (Spec Page 10).
        """
        if token == self.mock_user["access_token"]:
            return self.mock_user
        return {"error": "unauthorized"}

    def get_issued_documents(self, token: str):
        """
        Simulates GET /oauth2/2/files/issued (Spec Page 14).
        """
        if token == self.mock_user["access_token"]:
            return self.mock_documents
        return {"error": "unauthorized"}

    def get_file_xml(self, uri: str, token: str):
        """
        Simulates GET /oauth2/1/xml/uri (Spec Page 17).
        This is the KEY function for Module C (Automation).
        """
        if token != self.mock_user["access_token"]:
            return "<Error>Unauthorized</Error>"

        # Return clean XML data based on the URI
        if "HSCM" in uri:
            # Matches valid XML structure for automation parsing
            return """
            <Certificate name="Class XII Marksheet">
                <StudentDetails>
                    <Name>Remy Baastin Rayappan</Name>
                    <DOB>31-07-2005</DOB>
                    <RollNo>120863261</RollNo>
                </StudentDetails>
                <Marks>
                    <Subject name="Physics">92</Subject>
                    <Subject name="Chemistry">88</Subject>
                    <Subject name="Maths">95</Subject>
                    <Subject name="Computer Science">98</Subject>
                </Marks>
                <FinalResult>PASS</FinalResult>
            </Certificate>
            """
        elif "ADHAR" in uri:
             return """
            <KycRes>
                <UidData>
                    <Poi name="Remy Baastin Rayappan" dob="31-07-2005" gender="M"/>
                    <Poa co="S/O Jancy Sickory Daisy" house="1/5, GA Canal" dist="Thanjavur" state="Tamil Nadu" pc="613001"/>
                </UidData>
            </KycRes>
            """
        return "<Error>Document Not Found</Error>"