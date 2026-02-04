from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os

# 1. Define the "Brain" Logic (Same as RAG Service)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 2. Define the Knowledge (The Schemes)
# In a real app, you would load this from PDFs or a CSV.
schemes = [
    {
        "name": "PM Kisan Samman Nidhi",
        "text": "PM Kisan Samman Nidhi is a central sector scheme with 100% funding from Government of India. Under the scheme an income support of 6,000/- per year in three equal installments will be provided to small and marginal farmer families having combined land holding/ownership of upto 2 hectares. Definition of family for the scheme is husband, wife and minor children. State Government and UT administration will identify the farmer families which are eligible for support as per scheme guidelines. The fund will be directly transferred to the bank accounts of the beneficiaries."
    },
    {
        "name": "Post Matric Scholarship for Minorities",
        "text": "Scholarship is awarded to students from minority communities for pursuing higher education from class XI to Ph.D. Eligibility: Students must have secured not less than 50% marks or equivalent grade in the previous final examination. The annual income of the parents/guardian from all sources should not exceed Rs. 2.00 Lakh. 30% of scholarships are earmarked for girl students."
    },
    {
        "name": "AICTE Pragati Scholarship for Girls",
        "text": "The Pragati Scholarship is a scheme of the AICTE aimed at providing assistance for the advancement of girls pursuing technical education. Eligibility: The girl candidate should be admitted to the first year of a Diploma/Degree program of an AICTE approved institution. Maximum two girls per family are eligible. Family income should not be more than Rs. 8 Lakh per annum. Amount: Rs. 50,000 per annum for every year of study."
    },
    {
        "name": "National Means-cum-Merit Scholarship (NMMS)",
        "text": "The objective of the NMMS scheme is to award scholarships to meritorious students of economically weaker sections to arrest their drop out at class VIII and encourage them to continue the study at secondary stage. Scholarship of Rs. 12000/- per annum (Rs. 1000/- per month) per student is awarded to selected students of class IX every year and their renewal in classes X to XII. Parental income ceiling is Rs. 3.5 Lakh per annum."
    },
    {
        "name": "Dr. Ambedkar Post Matric Scholarship for EBC Students",
        "text": "This is a centrally sponsored scheme to provide financial assistance to the Economically Backward Class (EBC) students studying at post-matriculation or post-secondary stage to enable them to complete their education. The income ceiling of parents/guardians should not exceed Rs. 1.00 Lakh per annum."
    }
]

# 3. Convert Text to "Documents"
documents = []
for scheme in schemes:
    doc = Document(
        page_content=scheme["text"],
        metadata={"scheme_name": scheme["name"]}
    )
    documents.append(doc)

print(f"🚀 Seeding {len(documents)} schemes into the Knowledge Base...")

# 4. Create the Vector Store
db = FAISS.from_documents(documents, embeddings)

# 5. Save to Disk
db.save_local("faiss_index")

print("✅ Knowledge Base saved to 'faiss_index' folder!")