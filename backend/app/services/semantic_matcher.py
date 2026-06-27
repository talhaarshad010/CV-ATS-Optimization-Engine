import logging
import torch
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

# Global cached instance of the SentenceTransformer model
_model = None

def get_model() -> SentenceTransformer:
    """Lazily loads and caches the SentenceTransformer model."""
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def compute_semantic_score(cv_text: str, jd_text: str) -> float:
    """
    Computes semantic similarity score between CV text and Job Description text.
    Returns a score bounded between 0.0 and 1.0.
    """
    if not cv_text or not jd_text:
        return 0.0
        
    try:
        model = get_model()
        cv_emb = model.encode(cv_text, convert_to_tensor=True)
        jd_emb = model.encode(jd_text, convert_to_tensor=True)
        
        similarity = util.cos_sim(cv_emb, jd_emb).item()
        return float(max(0.0, min(1.0, similarity)))
    except Exception as e:
        logger.error(f"Error computing semantic score: {e}", exc_info=True)
        return 0.0


def compute_skill_match(cv_skills: list[str], jd_skills: list[str]) -> dict:
    """
    Evaluates skill matches between CV skills and required Job Description skills.
    Returns matched skills, missing skills, match percentage, and detail logs.
    """
    if not jd_skills:
        return {
            "matched": [],
            "missing": [],
            "match_percentage": 100.0,
            "details": []
        }
        
    if not cv_skills:
        return {
            "matched": [],
            "missing": list(jd_skills),
            "match_percentage": 0.0,
            "details": [
                {"skill": skill, "matched": False, "score": 0.0}
                for skill in jd_skills
            ]
        }
        
    model = get_model()
    
    matched_skills = []
    missing_skills = []
    details = []
    
    cv_skills_lower = [s.lower() for s in cv_skills]
    cv_embeddings = None
    
    for jd_skill in jd_skills:
        jd_skill_lower = jd_skill.lower()
        
        # 1. Exact Match Check (case-insensitive)
        if jd_skill_lower in cv_skills_lower:
            matched_skills.append(jd_skill)
            details.append({
                "skill": jd_skill,
                "matched": True,
                "score": 1.0,
                "match_type": "exact"
            })
            continue
            
        # 2. Semantic Match Check
        if cv_skills:
            try:
                if cv_embeddings is None:
                    cv_embeddings = model.encode(cv_skills, convert_to_tensor=True)
                    
                jd_emb = model.encode(jd_skill, convert_to_tensor=True)
                cos_scores = util.cos_sim(jd_emb, cv_embeddings)[0]
                
                max_idx = torch.argmax(cos_scores).item()
                max_score = cos_scores[max_idx].item()
                
                if max_score > 0.75:
                    matched_skills.append(jd_skill)
                    details.append({
                        "skill": jd_skill,
                        "matched": True,
                        "score": 0.8,
                        "match_type": "semantic",
                        "matched_with": cv_skills[max_idx],
                        "similarity": round(max_score, 2)
                    })
                    continue
            except Exception as e:
                logger.error(f"Error checking semantic skill match for '{jd_skill}': {e}")
                
        # 3. No Match
        missing_skills.append(jd_skill)
        details.append({
            "skill": jd_skill,
            "matched": False,
            "score": 0.0,
            "match_type": "none"
        })
        
    # Calculate weighted match percentage based on match scores
    sum_scores = sum(item["score"] for item in details)
    match_percentage = round((sum_scores / len(jd_skills)) * 100, 1)
    
    return {
        "matched": matched_skills,
        "missing": missing_skills,
        "match_percentage": match_percentage,
        "details": details
    }


def compute_experience_match(cv_years: float, required_years: int) -> float:
    """
    Scores CV years of experience against the required job description years.
    Returns scoring weights between 0.3 and 1.0.
    """
    if required_years is None:
        return 1.0
        
    if cv_years is None:
        cv_years = 0.0
        
    if cv_years >= required_years:
        return 1.0
    elif cv_years >= required_years * 0.8:
        return 0.8
    elif cv_years >= required_years * 0.5:
        return 0.5
    else:
        return 0.3
