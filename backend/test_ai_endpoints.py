import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = TestClient(app)

# Sample Mock Data
MOCK_CANDIDATE_ID = "71de1aa9-b3e1-4069-b723-b26769ddfdd8"
MOCK_JOB_ID = "88de1aa9-b3e1-4069-b723-b26769ddfdd8"

mock_candidate = {
    "id": MOCK_CANDIDATE_ID,
    "raw_text": "Muhammad Talha Arshad. Senior Developer with 4 years of experience. Python, Django.",
    "total_experience_years": 4.0,
    "raw_sections": {
        "experience": {
            "text": "Developed backend APIs with Django.\nCollaborated with frontend devs."
        }
    }
}

mock_skills = [
    {"skill_normalized": "Python", "confidence": 1.0},
    {"skill_normalized": "Django", "confidence": 1.0}
]

mock_jd = {
    "id": MOCK_JOB_ID,
    "title": "Senior Python Developer",
    "raw_text": "Required: Python, Django, Docker, AWS. 3 years experience.",
    "parsed_data": {
        "job_title": "Senior Python Developer",
        "required_skills": ["Python", "Django"],
        "preferred_skills": ["Docker", "AWS"],
        "required_experience_years": 3,
        "required_education": "Bachelor"
    }
}

# Define a mock class for the Supabase query response
class MockExecuteResponse:
    def __init__(self, data):
        self.data = data

@patch("app.routers.ai.get_candidate")
@patch("app.routers.ai.get_candidate_skills")
@patch("app.routers.ai.get_job_description")
@patch("app.routers.ai.supabase")
def test_ai_endpoints(mock_supabase, mock_get_jd, mock_get_skills, mock_get_candidate):
    # Configure mocks
    mock_get_candidate.return_value = mock_candidate
    mock_get_skills.return_value = mock_skills
    mock_get_jd.return_value = mock_jd
    
    # Configure Supabase mock to return empty list (triggers on-the-fly computation)
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = MockExecuteResponse(data=[])

    logger.info("1. Testing Bullet Points Rewriter endpoint...")
    rewrite_resp = client.post(f"/api/v1/ai/rewrite/{MOCK_CANDIDATE_ID}?job_title=Python+Developer")
    logger.info(f"Rewrite Response Code: {rewrite_resp.status_code}")
    logger.info(f"Rewrite Response Data: {rewrite_resp.json()}")
    assert rewrite_resp.status_code == 200
    assert "original_bullets" in rewrite_resp.json()
    assert "rewritten_bullets" in rewrite_resp.json()
    assert len(rewrite_resp.json()["original_bullets"]) == 2

    logger.info("\n2. Testing Skill Gaps Analyzer endpoint...")
    gaps_resp = client.post("/api/v1/ai/gaps", json={
        "candidate_id": MOCK_CANDIDATE_ID,
        "job_id": MOCK_JOB_ID
    })
    logger.info(f"Gaps Response Code: {gaps_resp.status_code}")
    logger.info(f"Gaps Response Data: {gaps_resp.json()}")
    assert gaps_resp.status_code == 200
    assert "gaps" in gaps_resp.json()
    assert "total_gaps" in gaps_resp.json()

    logger.info("\n3. Testing RAG Chatbot endpoint...")
    chat_resp = client.post("/api/v1/ai/chat", json={
        "question": "What is Muhammad Talha's main background?",
        "candidate_id": MOCK_CANDIDATE_ID
    })
    logger.info(f"Chat Response Code: {chat_resp.status_code}")
    logger.info(f"Chat Response Data: {chat_resp.json()}")
    assert chat_resp.status_code == 200
    assert "answer" in chat_resp.json()
    assert "sources" in chat_resp.json()

    logger.info("\n4. Testing Comprehensive Report endpoint...")
    report_resp = client.post(f"/api/v1/ai/report/{MOCK_CANDIDATE_ID}/{MOCK_JOB_ID}")
    logger.info(f"Report Response Code: {report_resp.status_code}")
    logger.info(f"Report Response Data: {report_resp.json()}")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert "ats_score" in report_data
    assert "grade" in report_data
    assert "skill_gaps" in report_data
    assert "rewritten_bullets" in report_data
    assert "action_plan" in report_data

    logger.info("\n✔ All GenAI endpoint unit tests passed successfully!")

if __name__ == "__main__":
    test_ai_endpoints()
