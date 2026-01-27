from app.services.vector_store import SchemeDatabase

if __name__ == "__main__":
    db = SchemeDatabase()
    
    # Ensure your file is named 'schemes.csv' and is in the backend folder
    db.ingest_from_csv("schemes.csv")