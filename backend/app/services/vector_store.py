import pandas as pd
import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

class SchemeDatabase:
    def __init__(self):
        self.persist_directory = "./chroma_db"
        
        # 🟢 SMART GPU SELECTOR
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            print("🚀 POWER ON: Using NVIDIA RTX 3050 for Embeddings")
        else:
            device = "cpu"
            print("⚠️ GPU not found. Falling back to CPU.")

        # This configures the model to run on the specific device
        model_kwargs = {'device': device}
        encode_kwargs = {'normalize_embeddings': False}
        
        print("Loading Embedding Model...")
        self.embedding_function = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        self.db = Chroma(
            persist_directory=self.persist_directory, 
            embedding_function=self.embedding_function
        )

    def ingest_from_csv(self, csv_path: str):
        """
        Reads 'schemes.csv' and saves it to the Vector Database.
        """
        if not os.path.exists(csv_path):
            print(f"❌ Error: Could not find {csv_path}")
            return

        print(f"--- 📖 Reading {csv_path} ---")
        try:
            df = pd.read_csv(csv_path)
            df = df.fillna("Not Specified") # Fix empty cells
        except Exception as e:
            print(f"❌ CSV Read Error: {e}")
            return

        documents = []
        for index, row in df.iterrows():
            # 4. Create the "Knowledge Block"
            # We combine all your key columns into one text block for the AI to read.
            content = f"""
            SCHEME NAME: {row.get('scheme_name', 'Unknown')}
            CATEGORY: {row.get('schemeCategory', 'General')}
            
            DETAILS: {row.get('details', '')}
            
            BENEFITS: {row.get('benefits', '')}
            
            ELIGIBILITY RULES: {row.get('eligibility', '')}
            
            REQUIRED DOCUMENTS: {row.get('documents', '')}
            
            APPLICATION PROCESS: {row.get('application', '')}
            """
            
            # 5. Add Metadata (Helps us filter results later if needed)
            metadata = {
                "source": "Sev-ai_Official",
                "name": row.get('scheme_name', 'Unknown'),
                "category": row.get('schemeCategory', 'General')
            }
            
            documents.append(Document(page_content=content, metadata=metadata))

        print(f"--- 💾 Ingesting {len(documents)} Schemes into Memory ---")
        
        # 6. Save to Database
        # batch_size=100 helps prevent crashes if you have 1000s of rows
        for i in range(0, len(documents), 100):
            batch = documents[i:i+100]
            self.db.add_documents(batch)
            print(f"   Processed batch {i} to {i+len(batch)}...")
            
        print("✅ Success! The Brain is updated.")

    def search_schemes(self, query: str, k=4):
        """
        Finds the top 'k' relevant schemes for a query.
        """
        return self.db.similarity_search(query, k=k)