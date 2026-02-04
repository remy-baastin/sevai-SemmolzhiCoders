import json
import os

DB_FILE = "user_db.json"

class DataService:
    def __init__(self):
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w') as f:
                json.dump({}, f)

    def _load_db(self):
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _save_db(self, data):
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def update_user_data(self, primary_key, new_data):
        if not primary_key: return {}
        
        db = self._load_db()
        key = primary_key.strip().lower()

        # --- MIGRATION LOGIC (The Fix) ---
        # If user exists but lacks the new structure, upgrade them.
        if key in db:
            if "profile" not in db[key] or "documents" not in db[key]:
                print(f"🔧 Migrating legacy data for user: {key}")
                old_data = db[key]
                db[key] = {
                    "profile": old_data, # Move old flat data into profile
                    "documents": []
                }
        else:
            # Create new user
            db[key] = {
                "profile": {},
                "documents": []
            }

        # --- UPDATE LOGIC ---
        
        # 1. Update Profile (Standard Fields)
        std_data = new_data.get("standardized_data", {})
        # Safety check: ensure std_data is actually a dict
        if isinstance(std_data, dict):
            for field, value in std_data.items():
                if value:
                    db[key]["profile"][field] = value

        # 2. Add Document Record (Specifics)
        doc_entry = {
            "type": new_data.get("document_type", "Unknown"),
            "data": new_data.get("specific_data", {})
        }
        
        # Prevent duplicate document entries
        if doc_entry not in db[key]["documents"]:
            db[key]["documents"].append(doc_entry)

        self._save_db(db)
        print(f"💾 Database Updated for: {primary_key}")
        return db[key]

    def get_user_data(self, primary_key):
        db = self._load_db()
        key = primary_key.strip().lower()
        return db.get(key, {})