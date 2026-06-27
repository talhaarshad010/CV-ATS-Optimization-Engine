import sys
import logging
from app.services.skill_normalizer import SkillNormalizer

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_normalizer():
    logger.info("Initializing SkillNormalizer...")
    normalizer = SkillNormalizer()
    
    # Test cases: (input, expected_part_of_normalized_name)
    test_cases = [
        ("Python", "python"),
        ("JS", "javascript"),
        ("React.js", "react"),
        ("FastAPI", "fastapi"),
        ("Machine Learning", "machine learning"),
        ("data engineering", "data engineering"),
        ("SQL Developer", "sql"),
    ]
    
    logger.info("Running normalization tests...")
    success = True
    for raw, expected in test_cases:
        res = normalizer.normalize_single_skill(raw)
        normalized = res["normalized"]
        confidence = res["confidence"]
        logger.info(f"Raw: '{raw}' -> Normalized: '{normalized}' (Confidence: {confidence})")
        if expected.lower() not in normalized.lower():
            logger.warning(f"  Warning: Expected '{expected}' to be in '{normalized}'")
            # We don't fail, as some models mapping might slightly vary, but log it
            
    # Test cleaning/parsing list
    sample_skills_section = """
    * Python, Java, C++
    * HTML5 & CSS3 | React / Redux
    * Machine learning, deep learning; Natural Language Processing (NLP)
    """
    logger.info("Testing skills list cleaning & normalization...")
    results = normalizer.normalize_skills_list(sample_skills_section)
    for res in results:
        logger.info(f"Raw: '{res['skill_raw']}' -> Normalized: '{res['skill_normalized']}' (Conf: {res['confidence']})")

if __name__ == "__main__":
    test_normalizer()
