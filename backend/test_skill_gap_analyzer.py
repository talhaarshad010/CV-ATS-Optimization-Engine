import sys
import logging
from app.services.skill_gap_analyzer import analyze_gaps, generate_improvement_plan

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_gap_analyzer():
    logger.info("Starting Skill Gap Analyzer test...")
    
    # 1. Test Gap Analysis
    missing_skills = ["Docker", "Kubernetes"]
    candidate_skills = ["Python", "Django", "PostgreSQL", "Git"]
    job_title = "Senior Python Developer"
    
    logger.info("Analyzing skill gaps...")
    gaps_result = analyze_gaps(missing_skills, candidate_skills, job_title)
    
    logger.info(f"Gaps Output: {gaps_result}")
    assert "gaps" in gaps_result
    assert gaps_result["total_gaps"] == 2
    assert "estimated_total_weeks" in gaps_result
    
    for gap in gaps_result["gaps"]:
        assert "skill" in gap
        assert "priority" in gap
        assert "suggested_course" in gap
        assert "suggested_project" in gap
        assert "estimated_weeks" in gap

    # 2. Test Action Plan Generation
    ats_score = 74
    breakdown = {
        "skill_match": {"score": 25, "max": 30, "percentage": 83.3},
        "experience_match": {"score": 20, "max": 20, "percentage": 100.0},
        "education_match": {"score": 12, "max": 15, "percentage": 80.0},
        "semantic_similarity": {"score": 11, "max": 15, "percentage": 70.8},
        "project_relevance": {"score": 1, "max": 10, "percentage": 10.0},
        "certifications": {"score": 5, "max": 5, "percentage": 100.0},
        "resume_quality": {"score": 4, "max": 5, "percentage": 80.0}
    }
    
    logger.info("Generating improvement plan...")
    plan = generate_improvement_plan(ats_score, breakdown, gaps_result)
    logger.info(f"Generated 5-Step Plan:\n{plan}")
    
    assert len(plan) > 0
    assert "1." in plan or "1 " in plan
    assert "5." in plan or "5 " in plan
    
    logger.info("✔ Skill Gap Analyzer unit tests passed successfully!")

if __name__ == "__main__":
    test_gap_analyzer()
