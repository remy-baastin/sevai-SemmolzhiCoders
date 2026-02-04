import os
import json
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from app.services.data_service import DataService
from langchain_groq import ChatGroq

class RAGService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ CRITICAL: GROQ_API_KEY is missing!")

        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.db_path = "chroma_db"
        
        if os.path.exists(self.db_path):
            try:
                self.vector_store = Chroma(
                    persist_directory=self.db_path, 
                    embedding_function=self.embeddings
                )
            except:
                 self.vector_store = None
        else:
            self.vector_store = None

        self.llm = ChatGroq(
            temperature=0,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=api_key
        )
        self.data_store = DataService()

    def recommend_schemes(self, simple_profile, user_query, history):
        try:
            user_name = getattr(simple_profile, 'name', str(simple_profile)) 
        except:
            user_name = "Unknown"

        # 1. Fetch User Data
        rich_user_data = self.data_store.get_user_data(user_name)
        context_str = json.dumps(rich_user_data, indent=2)

        # 2. RAG Search
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search(user_query, k=4) 
                scheme_context = "\n".join([d.page_content for d in docs])
            except:
                scheme_context = "Database search failed."
        else:
            scheme_context = "No specific scheme database found."

        # --- THE FIX: CONFIRMATION LOGIC ADDED ---
        template = """
        You are Sev-ai, an intelligent government scheme assistant.
        
        --- USER CONTEXT (DATABASE) ---
        {user_data}
        
        --- SKILLS ---
        1. **PAN Card** (Target: "PAN Card") - Requires: Name, DOB, Mobile, Email.
        
        --- HISTORY ---
        {history}

        --- CURRENT USER MESSAGE ---
        {query}
        
        --- INSTRUCTIONS ---
        1. **Check Data Status:** Look at the "USER CONTEXT". Do we have Name, DOB, Mobile, and Email?
        2. **Analyze User Intent:**
           - **New Data:** If user provides missing info (e.g., "Email is..."), extract it.
           - **Confirmation:** If user says "Yes", "Correct", "Proceed", or "Apply" AND we have all required data (Name, DOB, Mobile, Email), then **TRIGGER RPA**.
           - **Request:** If user asks for PAN but data is missing, ask for the specific missing field.
        
        3. **Decision Logic (PAN Card):**
           - IF (Intent is Apply OR Confirmation) AND (All Data Present) -> ACTION: "TRIGGER_RPA".
           - IF (Intent is Apply) AND (Data Missing) -> Ask user for missing data.
           - IF (User provided Data) -> Extract it, and if profile is now complete, ACTION: "TRIGGER_RPA".

        --- OUTPUT FORMAT (STRICT JSON) ---
        {{
            "response_text": "Friendly response...",
            "extracted_data": {{ "email": "...", "mobile": "..." }} (or null),
            "action": "TRIGGER_RPA" or "NONE",
            "target_scheme": "PAN Card" (or null),
            "missing_data": []
        }}
        """

        prompt = PromptTemplate(
            input_variables=["user_data", "scheme_info", "query", "history"],
            template=template
        )

        chain = prompt | self.llm
        try:
            # JOIN HISTORY INTO A STRING
            history_str = "\n".join(history) if history else "No previous chat."

            response = chain.invoke({
                "user_data": context_str, 
                "scheme_info": scheme_context,
                "query": user_query,
                "history": history_str  # <--- PASS HISTORY SO IT REMEMBERS THE QUESTION
            })
            
            content = response.content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                return content[json_start:json_end]
            return content

        except Exception as e:
            print(f"❌ Chatbot Error: {e}")
            return json.dumps({"response_text": "Error.", "action": "NONE"})