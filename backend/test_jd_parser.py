import sys
import logging
from app.services.jd_parser import parse_jd

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_jd_parsing():
    sample_jd = """
    # Senior Python Developer
    
    We are looking for a Senior Python Developer with at least 3 years of experience.
    
    Qualifications:
    * Bachelor's degree in Computer Science or related field
    * Master's degree is a plus
    
    Required Skills:
    - Python, Django, PostgreSQL
    - Git & GitHub
    
    Preferred Skills:
    - Docker, AWS, Kubernetes
    
    Responsibilities:
    - Build REST APIs using FastAPI and Django
    - Manage deployments and CI/CD pipelines
    - Lead and mentor junior developers
    """
    
    logger.info("Parsing sample Job Description...")
    result = parse_jd(sample_jd)
    
    logger.info(f"Extracted Job Title: {result['job_title']}")
    logger.info(f"Required Experience Years: {result['required_experience_years']}")
    logger.info(f"Required Education: {result['required_education']}")
    logger.info(f"Required Skills: {result['required_skills']}")
    logger.info(f"Preferred Skills: {result['preferred_skills']}")
    logger.info(f"Responsibilities: {result['responsibilities']}")
    
    # Assertions to verify correctness
    assert result['job_title'] == "Senior Python Developer", f"Expected 'Senior Python Developer', got '{result['job_title']}'"
    assert result['required_experience_years'] == 3, f"Expected 3, got {result['required_experience_years']}"
    assert result['required_education'] == "Bachelor", f"Expected 'Bachelor', got '{result['required_education']}'"
    assert "Python" in result['required_skills'], "Expected 'Python' in required skills"
    assert "Docker" in result['preferred_skills'], "Expected 'Docker' in preferred skills"
    assert len(result['responsibilities']) > 0, "Expected responsibilities to not be empty"
    
    logger.info("✔ All local parser assertions passed!")

if __name__ == "__main__":
    test_jd_parsing()
