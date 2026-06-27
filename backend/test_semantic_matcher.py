import sys
import logging
from app.services.semantic_matcher import compute_semantic_score, compute_skill_match, compute_experience_match

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_semantic_matcher():
    # 1. Test Experience Matching
    logger.info("Testing Experience Matcher...")
    assert compute_experience_match(5.0, 5) == 1.0
    assert compute_experience_match(4.0, 5) == 0.8  # 4 is 80% of 5
    assert compute_experience_match(3.0, 5) == 0.5  # 3 is 60% of 5 (>= 50%)
    assert compute_experience_match(2.0, 5) == 0.3  # 2 is 40% of 5 (< 50%)
    assert compute_experience_match(3.0, None) == 1.0
    logger.info("✔ Experience Matcher tests passed!")

    # 2. Test Skill Matching
    logger.info("Testing Skill Matcher...")
    cv_skills = ["Python Programming", "Frontend Developer", "PostgreSQL", "Git"]
    jd_skills = ["Python", "Frontend Development", "Docker", "Git"]
    
    result = compute_skill_match(cv_skills, jd_skills)
    logger.info(f"Skill Match Results: {result}")
    
    # Python & Frontend Development match semantically (score 0.8 each)
    # Git matches exactly (score 1.0)
    # Docker is missing (score 0.0)
    # Sum scores = 0.8 + 0.8 + 1.0 + 0.0 = 2.6. percentage = 2.6 / 4 * 100 = 65.0%
    assert "Python" in result["matched"]
    assert "Frontend Development" in result["matched"]
    assert "Docker" in result["missing"]
    assert result["match_percentage"] == 65.0

    logger.info("✔ Skill Matcher tests passed!")

    # 3. Test Semantic Text Similarity
    logger.info("Testing Semantic Text Similarity...")
    cv_text = "I am a Senior Backend Engineer working with Python, Django, PostgreSQL, building high-performance REST APIs."
    jd_text = "Looking for a Senior Software Developer who builds web backends in Python and SQL databases."
    diff_jd_text = "We need an iOS Mobile Designer with experience in Figma, Sketch, and typography."
    
    sim_score_similar = compute_semantic_score(cv_text, jd_text)
    sim_score_different = compute_semantic_score(cv_text, diff_jd_text)
    
    logger.info(f"Similarity (similar profiles): {sim_score_similar}")
    logger.info(f"Similarity (different profiles): {sim_score_different}")
    
    assert sim_score_similar > sim_score_different
    assert 0.0 <= sim_score_similar <= 1.0
    assert 0.0 <= sim_score_different <= 1.0
    logger.info("✔ Semantic Text Similarity tests passed!")

if __name__ == "__main__":
    test_semantic_matcher()
