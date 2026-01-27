from app.services.rag_service import RAGService
import time

def test_brain():
    # 1. Initialize
    rag = RAGService()
    
    # 2. Simulate a User (Mocking the DigiLocker XML we got earlier)
    # This user is a 19-year-old Student
    mock_user_xml = """
    <User>
        <Name>Remy Baastin</Name>
        <Age>19</Age>
        <Gender>Male</Gender>
        <Occupation>Student</Occupation>
        <Caste>SC</Caste>
        <Income>150000</Income>
        <Education>Class 12 Pass</Education>
    </User>
    """
    
    # 3. Ask a question
    query = "I need a scholarship for my college studies."
    
    print("\n--- 🧪 STARTING TEST ---")
    start_time = time.time()
    
    response = rag.recommend_schemes(mock_user_xml, query)
    
    end_time = time.time()
    print("\n--- 🤖 AI RESPONSE ---")
    print(response)
    print(f"\n⏱️ Time Taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    test_brain()