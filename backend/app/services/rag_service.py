'''
from app.services.vector_store import SchemeDatabase
from langchain_community.llms import Ollama
import json

class RAGService:
    def __init__(self):
        # Connect to your GPU-powered Scheme Database
        self.db = SchemeDatabase()
        
        # Connect to your local Llama 3 model
        # temperature=0 makes the bot strict and factual (good for government rules)
        print("🤖 Initializing Llama 3 Brain...")
        self.llm = Ollama(model="llama3", temperature=0)

    def recommend_schemes(self, user_xml_data: str, user_query: str):
        """
        The Core Logic:
        1. Reads User Data (XML)
        2. Finds relevant schemes (Vector Search)
        3. Asks Llama 3 to check eligibility
        """
        
        # Step 1: Search for relevant schemes
        # We combine the query with a bit of user context to improve search
        search_query = f"{user_query} {user_xml_data[:200]}" # Use first 200 chars of profile for context
        print(f"🔍 Searching database for: {user_query}...")
        
        relevant_schemes = self.db.search_schemes(search_query, k=4)
        
        # Prepare the "Context" text for the AI
        schemes_context = "\n\n".join([doc.page_content for doc in relevant_schemes])
        
        # Step 2: Construct the "Judge" Prompt
        prompt = f"""
        You are an expert Government Scheme Advisor for India.
        
        USER PROFILE (Verified Data):
        {user_xml_data}
        
        AVAILABLE SCHEMES (Reference Data):
        {schemes_context}
        
        USER QUESTION: 
        "{user_query}"
        
        INSTRUCTIONS:
        1. Analyze the User Profile against the Eligibility Rules of the schemes provided above.
        2. STRICTLY check if the user meets criteria like Age, Income, Caste, or Gender.
        3. If they are eligible, explain WHY and list the BENEFITS.
        4. If they are NOT eligible, explain exactly what is missing (e.g., "Income too high").
        5. List the required documents from the scheme details.

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "eligible": true/false,
            "scheme_name": "Name of best match",
            "reason": "Clear explanation of eligibility",
            "benefits": "What they get",
            "missing_documents": ["Doc 1", "Doc 2"]
        }}
        """

        # Step 3: Generate Answer
        print("🧠 Llama 3 is thinking...")
        response = self.llm.invoke(prompt)
        return response
        
        '''

from app.services.vector_store import SchemeDatabase
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

class RAGService:
    def __init__(self):
        # 1. Load Environment Variables
        from dotenv import load_dotenv
        load_dotenv() # This looks for a .env file
        
        # 2. Connect to Database
        self.db = SchemeDatabase()
        
        # 3. Get Key & DEBUG PRINT
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        # --- DEBUG CHECK ---
        if not groq_api_key:
            print("❌ FATAL ERROR: Could not find GROQ_API_KEY in .env file!")
            print("   -> Make sure the file is named exactly '.env' (not .env.txt)")
            print("   -> Make sure it is inside the 'backend' folder.")
            return # Stop here
        else:
            print(f"✅ Success! Found API Key: {groq_api_key[:5]}******")
        # -------------------

        print("☁️  Connecting to Groq Cloud (Llama 3.3)...")
        try:
            self.llm = ChatGroq(
                temperature=0, 
                model_name="llama-3.3-70b-versatile",
                api_key=groq_api_key
            )
        except Exception as e:
            print(f"❌ Groq Connection Error: {e}")

    def recommend_schemes(self, user_xml_data: str, user_query: str):
        # Step 1: Search Database
        search_query = f"{user_query} {user_xml_data[:200]}"
        print(f"🔍 Searching database for: {user_query}...")
        
        relevant_schemes = self.db.search_schemes(search_query, k=4)
        schemes_context = "\n\n".join([doc.page_content for doc in relevant_schemes])
        
        # Step 2: Construct Prompt
        prompt = f"""
        You are an expert Government Scheme Advisor for India.
        
        USER PROFILE (Verified Data):
        {user_xml_data}
        
        AVAILABLE SCHEMES (Context):
        {schemes_context}
        
        USER QUESTION: "{user_query}"
        
        INSTRUCTIONS:
        1. Analyze the User Profile against the Eligibility Rules of the schemes.
        2. STRICTLY check criteria like Age, Income, Caste, or Gender.
        3. If eligible, explain WHY and list BENEFITS.
        4. If NOT eligible, explain exactly what is missing.

        FORMAT YOUR RESPONSE AS JSON ONLY:
        {{
            "eligible": true/false,
            "scheme_name": "Name of best match",
            "reason": "Clear explanation",
            "benefits": "Summary of benefits",
            "missing_documents": ["Doc 1", "Doc 2"]
        }}
        """

        # Step 3: Get Answer
        print("🧠 Cloud Brain is thinking...")
        try:
            response = self.llm.invoke(prompt)
            content = response.content
            
            # 🧹 CLEANUP: Remove the ```json and ``` marks
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return clean_content
            
        except Exception as e:
            return f'{{"error": "Error connecting to Brain: {e}"}}'