from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import pandas as pd
import os
import shutil
import torch
from tqdm import tqdm

# Define where the database lives
DB_DIR = "chroma_db"
BATCH_SIZE = 100

def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"

def ingest_data():
    # 1. Clean Slate
    if os.path.exists(DB_DIR):
        print(f"🧹 Clearing old database at {DB_DIR}...")
        try:
            shutil.rmtree(DB_DIR)
        except Exception as e:
            print(f"⚠️ Could not delete old DB: {e}")

    # 2. Setup High-Performance Embeddings
    device = get_device()
    print(f"🚀 Acceleration Mode: {device.upper()}")
    
    model_kwargs = {'device': device}
    encode_kwargs = {'normalize_embeddings': True, 'batch_size': 32}

    print("🧠 Initializing Embedding Model (MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    # 3. Load Data
    csv_file = "updated_data.csv"
    if not os.path.exists(csv_file):
        print(f"❌ Error: '{csv_file}' not found.")
        return

    print("📂 Reading CSV file...")
    try:
        # THE FIX: dtype=str forces everything to be text, preventing the float error
        df = pd.read_csv(csv_file, dtype=str)
        df.fillna("Not Specified", inplace=True)
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # 4. Create Documents
    documents = []
    print(f"📄 Preparing {len(df)} documents...")

    for index, row in df.iterrows():
        page_content = f"""
        Scheme Name: {row.get('scheme_name', 'Unknown')}
        Category: {row.get('schemeCategory', 'Unknown')}
        Level: {row.get('level', 'Unknown')}
        
        Details:
        {row.get('details', '')}
        
        Benefits:
        {row.get('benefits', '')}
        
        Eligibility:
        {row.get('eligibility', '')}
        
        Documents Required:
        {row.get('documents', '')}
        """
        
        metadata = {
            "scheme_name": row.get('scheme_name', 'Unknown'),
            "category": row.get('schemeCategory', 'Unknown'),
            "level": row.get('level', 'Unknown')
        }
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)

    # 5. Ingest in Batches
    print(f"⚙️ Ingesting into ChromaDB in batches of {BATCH_SIZE}...")
    
    if documents:
        vector_db = Chroma(
            embedding_function=embeddings,
            persist_directory=DB_DIR
        )
        
        total_docs = len(documents)
        for i in tqdm(range(0, total_docs, BATCH_SIZE), desc="Embedding Batches"):
            batch = documents[i : i + BATCH_SIZE]
            vector_db.add_documents(batch)
            
        print(f"✅ Success! Knowledge Base with {total_docs} schemes saved to '{DB_DIR}'.")
    else:
        print("⚠️ No documents found to ingest.")

if __name__ == "__main__":
    ingest_data()