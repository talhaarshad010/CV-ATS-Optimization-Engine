import sys
import logging
from app.services.ats_scorer import compute_ats_score, explain_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_ats_scorer_explain():
    logger.info("Initializing mock data for ATS explainability test...")
    
    mock_candidate = {
        "raw_text": "MUHAMMAD TALHA ARSHAD. Senior Backend Engineer with Python, Django, PostgreSQL, Git, and Docker. Experience: 4 years.",
        "total_experience_years": 4.0,
        "skills": [
            {"normalized": "Python"},
            {"normalized": "Django"},
            {"normalized": "PostgreSQL"},
            {"normalized": "Git"},
            {"normalized": "Docker"}
        ],
        "raw_sections": {
            "summary": {"confidence": "high", "text": "Experienced Python Developer"},
            "education": {"confidence": "high", "text": "BS in Computer Science"},
            "experience": {"confidence": "high", "text": "4 years working on backend systems"},
            "skills": {"confidence": "high", "text": "Python, Django, PostgreSQL, Git, Docker"},
            "projects": {"confidence": "high", "text": "Built a large-scale CV parser and ATS scoring engine"},
            "certifications": {"confidence": "low", "text": "Certified Scrum Master"}
        }
    }
    
    mock_jd = {
        "job_title": "Senior Python Developer",
        "raw_text": "Required: Senior Python Developer. Minimum 3 years experience. Bachelor required. Skills: Python, Django, PostgreSQL, Git, Docker, Kubernetes, AWS.",
        "required_skills": ["Python", "Django", "PostgreSQL", "Git", "Docker", "Kubernetes", "AWS"],
        "preferred_skills": ["Google Cloud"],
        "required_experience_years": 3,
        "required_education": "Bachelor",
        "responsibilities": ["Build REST APIs", "Manage deployments"]
    }
    
    logger.info("Computing ATS Score Explanation...")
    explanation = explain_score(mock_candidate, mock_jd)
    
    logger.info(f"ATS Explanation Output: {explanation}")
    
    # Assertions
    assert "ats_score" in explanation
    assert "top_positives" in explanation
    assert "top_negatives" in explanation
    assert "recommendation" in explanation
    
    # Check structure of explanations list
    for pos in explanation["top_positives"]:
        assert "factor" in pos
        assert "impact" in pos
        assert "detail" in pos
        assert pos["impact"].startswith("+")
        
    for neg in explanation["top_negatives"]:
        assert "factor" in neg
        assert "impact" in neg
        assert "detail" in neg
        assert neg["impact"].startswith("-")
        
    assert "Kubernetes" in explanation["recommendation"] or "AWS" in explanation["recommendation"]
    
    logger.info("✔ ATS Scorer and SHAP Explainability tests passed successfully!")

if __name__ == "__main__":
    test_ats_scorer_explain()
