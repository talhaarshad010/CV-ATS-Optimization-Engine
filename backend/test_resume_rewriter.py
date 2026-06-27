import sys
import logging
from app.services.resume_rewriter import rewrite_bullet_points, improve_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_rewriter():
    logger.info("Starting Resume Rewriter test...")
    
    # 1. Test bullet point rewriting
    mock_experience = """
    * I worked on a python website and added database tables.
    * Helped users with their bugs.
    """
    job_title = "Senior Python Developer"
    
    logger.info("Rewriting bullet points...")
    bullets_result = rewrite_bullet_points(mock_experience, job_title)
    
    logger.info(f"Original Bullets: {bullets_result['original_bullets']}")
    logger.info(f"Rewritten Bullets: {bullets_result['rewritten_bullets']}")
    logger.info(f"Improvement Count: {bullets_result['improvement_count']}")
    
    assert len(bullets_result["original_bullets"]) == 2
    assert len(bullets_result["rewritten_bullets"]) == 2
    assert bullets_result["improvement_count"] == 2
    
    # 2. Test summary improvement
    mock_summary = "I am a fresh graduate who wants to write code in python. I have some projects."
    top_skills = ["Python", "Django", "PostgreSQL"]
    
    logger.info("Improving summary...")
    improved_summary = improve_summary(mock_summary, job_title, top_skills)
    logger.info(f"Original Summary: {mock_summary}")
    logger.info(f"Improved Summary: {improved_summary}")
    
    assert len(improved_summary) > 0
    assert improved_summary != mock_summary
    
    logger.info("✔ Resume Rewriter unit tests passed successfully!")

if __name__ == "__main__":
    test_rewriter()
