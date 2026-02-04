from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class UserProfile(BaseModel):
    # 1. Standard Fields (from DigiLocker/Input)
    name: str = "Guest"
    age: int = 18
    gender: str = "All"
    state: str = "India"
    caste: str = "General"
    income: int = 0
    occupation: str = "Student"
    
    # 2. NEW: Flexible Data (For things like Roll No, School Name, Kisan ID)
    verified_documents: Dict[str, Any] = Field(default_factory=dict)

    def to_search_context(self) -> str:
        # We add the verified docs to the search context so the DB can find relevant schemes
        docs_str = ", ".join([f"{k}: {v}" for k, v in self.verified_documents.items()])
        
        return (
            f"Government schemes for a {self.age} year old {self.gender} "
            f"{self.caste} caste {self.occupation} "
            f"with income {self.income}. "
            f"Has verified documents: {docs_str}."
        )

class ChatRequest(BaseModel):
    user_profile: UserProfile
    query: str
    history: Optional[List[Dict[str, str]]] = []