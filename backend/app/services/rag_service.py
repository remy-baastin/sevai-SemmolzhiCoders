from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from app.services.vector_store import SchemeDatabase
import os
import json
from dotenv import load_dotenv

class RAGService:
    def __init__(self):
        load_dotenv()
        
        # 1. Initialize Groq (The Brain)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ ERROR: GROQ_API_KEY not found in .env file.")
        
        # Initialize Llama 3 via Groq
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # 2. Initialize Database (The Memory)
        self.db = SchemeDatabase()

    def recommend_schemes(self, user: 'UserProfile', user_query: str, history: list = []):
        
        # --- STEP 1: Format Chat History ---
        chat_history_text = ""
        if history:
            chat_history_text = "PREVIOUS CONVERSATION:\n"
            for turn in history[-3:]: # Keep last 3 turns
                chat_history_text += f"User: {turn.get('user', '')}\nAI: {turn.get('ai', '')}\n"

        # --- STEP 2: Format OCR Proofs ---
        # If OCR found Verified Documents, we list them here so the AI trusts them.
        doc_proofs = ""
        if hasattr(user, 'verified_documents') and user.verified_documents:
            doc_proofs = "\nVERIFIED DOCUMENTS (OCR SCANNED):"
            for doc, val in user.verified_documents.items():
                doc_proofs += f"\n- {doc}: {val} (Verified)"

        # --- STEP 3: Search Database ---
        # Search using natural language profile + query
        search_context = user.to_search_context()
        full_query = f"{user_query} {search_context}"
        
        print(f"🔍 Searching DB for: {user_query}...")
        relevant_schemes = self.db.search_schemes(full_query, k=4)
        schemes_text = "\n\n".join([doc.page_content for doc in relevant_schemes])
        
        # --- STEP 4: The Master Prompt ---
        prompt = f"""
        You are Sev-ai, an intelligent Government Scheme Advisor.
        
        {chat_history_text}

        USER PROFILE:
        - Age: {user.age} | Gender: {user.gender}
        - Caste: {user.caste} | Income: ₹{user.income}
        - Occupation: {user.occupation}
        - State: {user.state}
        {doc_proofs}
        
        AVAILABLE SCHEMES (From Database):
        {schemes_text}
        
        USER QUERY: "{user_query}"
        
        INSTRUCTIONS:
        1. Check eligibility STRICTLY against the User Profile.
        2. If the user has a Verified Document (like Roll No or Kisan ID), USE IT to confirm eligibility.
        3. If a scheme requires a document they haven't uploaded, list it in "missing_documents".
        4. Output valid JSON only.

        FORMAT:
        {{
            "eligible": true/false,
            "scheme_name": "Best Matching Scheme Name",
            "reason": "Clear explanation based on profile and docs.",
            "benefits": "Short summary of benefits.",
            "missing_documents": ["Doc 1", "Doc 2"]
        }}
        """

        # --- STEP 5: Run Inference ---
        print("🧠 Brain is thinking...")
        try:
            response = self.llm.invoke(prompt)
            # Clean up the response (remove ```json wrappers if model adds them)
            clean_content = response.content.replace("```json", "").replace("```", "").strip()
            return clean_content
        except Exception as e:
            print(f"❌ AI Error: {e}")
            return json.dumps({
                "eligible": False, 
                "scheme_name": "Error", 
                "reason": "AI Brain Connection Failed", 
                "benefits": "N/A"
            })