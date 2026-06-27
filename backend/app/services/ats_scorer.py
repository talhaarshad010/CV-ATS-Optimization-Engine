import logging
import numpy as np
import shap
from typing import Dict, Any, List

from app.services.semantic_matcher import (
    compute_semantic_score,
    compute_skill_match,
    compute_experience_match
)
from app.services.jd_parser import extract_education

logger = logging.getLogger(__name__)


def extract_cv_skills_list(candidate_data: Dict[str, Any]) -> List[str]:
    """Helper to extract flat list of skill strings from candidate data structure."""
    skills_input = candidate_data.get("skills", [])
    if not skills_input:
        return []
        
    skills_list = []
    for s in skills_input:
        if isinstance(s, dict):
            name = s.get("normalized") or s.get("skill_normalized") or s.get("skill_raw") or s.get("raw")
            if name:
                skills_list.append(name)
        elif isinstance(s, str):
            skills_list.append(s)
    return skills_list


def get_ats_grade(score: int) -> str:
    """Calculates the grade corresponding to the total ATS score."""
    if score >= 90:
        return "A"
    elif score >= 85:
        return "A-"
    elif score >= 80:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 70:
        return "B-"
    elif score >= 60:
        return "C"
    else:
        return "D"


def compute_ats_score(candidate_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a weighted ATS score based on:
    - 30% Skill match
    - 20% Experience match
    - 15% Education match
    - 15% Semantic similarity
    - 10% Project relevance
    - 5%  Certifications match
    - 5%  Resume quality
    """
    # 0. Preparation of texts
    cv_text = candidate_data.get("raw_text", "")
    
    # Reconstruct JD text if raw_text is not explicitly present in jd_data
    jd_text = jd_data.get("raw_text")
    if not jd_text:
        jd_text = f"{jd_data.get('job_title', '')}\n"
        jd_text += "\n".join(jd_data.get("responsibilities", []))
        jd_text += "\n" + " ".join(jd_data.get("required_skills", []))
        jd_text += "\n" + " ".join(jd_data.get("preferred_skills", []))
    
    # 1. Skill Match (30%)
    cv_skills = extract_cv_skills_list(candidate_data)
    jd_required_skills = jd_data.get("required_skills", [])
    
    skill_match_res = compute_skill_match(cv_skills, jd_required_skills)
    skill_pct = skill_match_res.get("match_percentage", 0.0)
    skill_score = (skill_pct / 100.0) * 30.0
    
    # 2. Experience Match (20%)
    cv_years = candidate_data.get("total_experience_years", 0.0)
    required_years = jd_data.get("required_experience_years")
    
    exp_weight = compute_experience_match(cv_years, required_years)
    exp_score = exp_weight * 20.0
    
    # 3. Education Match (15%)
    # Extract highest education from candidate's text
    cv_edu_section = candidate_data.get("raw_sections", {}).get("education", {}).get("text", "")
    cv_education = extract_education(cv_edu_section or cv_text)
    jd_education = jd_data.get("required_education")
    
    edu_weight = 1.0
    if jd_education:
        edu_hierarchy = {"Bachelor": 1, "Master": 2, "PhD": 3}
        cv_val = edu_hierarchy.get(cv_education, 0)
        jd_val = edu_hierarchy.get(jd_education, 0)
        
        if cv_val >= jd_val:
            edu_weight = 1.0
        elif cv_val == jd_val - 1:
            edu_weight = 0.8
        else:
            edu_weight = 0.5
    else:
        # If no education is required, candidate gets full points
        edu_weight = 1.0
        
    edu_score = edu_weight * 15.0
    
    # 4. Semantic Similarity (15%)
    similarity = compute_semantic_score(cv_text, jd_text)
    sim_score = similarity * 15.0
    
    # 5. Project Relevance (10%)
    cv_projects = candidate_data.get("raw_sections", {}).get("projects", {}).get("text", "")
    proj_weight = 0.0
    if cv_projects:
        proj_weight = compute_semantic_score(cv_projects, jd_text)
    
    proj_score = proj_weight * 10.0
    
    # 6. Certifications Match (5%)
    cv_certs = candidate_data.get("raw_sections", {}).get("certifications", {}).get("text", "").lower()
    jd_requires_certs = "certif" in jd_text.lower() or "license" in jd_text.lower()
    
    cert_weight = 0.8
    if jd_requires_certs:
        if len(cv_certs) > 10:
            cert_weight = 1.0
        elif any(k in cv_certs for k in ["certif", "certified", "license", "pmp", "scrum"]):
            cert_weight = 0.8
        else:
            cert_weight = 0.3
    else:
        if len(cv_certs) > 10:
            cert_weight = 1.0
            
    cert_score = cert_weight * 5.0
    
    # 7. Resume Quality (5%)
    # a. Completeness (completeness of essential sections)
    sections = candidate_data.get("raw_sections", {})
    essential_sections = ["summary", "education", "experience", "skills"]
    completed_count = sum(1 for s in essential_sections if sections.get(s, {}).get("confidence") == "high")
    completeness_ratio = completed_count / len(essential_sections) if essential_sections else 1.0
    
    # b. Text Length Score
    text_length = len(cv_text)
    length_weight = 1.0
    if text_length < 500 or text_length > 15000:
        length_weight = 0.6
    elif text_length < 1000 or text_length > 10000:
        length_weight = 0.8
        
    quality_weight = (completeness_ratio * 0.7) + (length_weight * 0.3)
    quality_score = quality_weight * 5.0
    
    # Sum up all weighted scores
    total_score = skill_score + exp_score + edu_score + sim_score + proj_score + cert_score + quality_score
    ats_score_int = int(round(total_score))
    
    # Build breakdown dictionary
    breakdown = {
        "skill_match": {
            "score": int(round(skill_score)),
            "max": 30,
            "percentage": round(skill_pct, 1)
        },
        "experience_match": {
            "score": int(round(exp_score)),
            "max": 20,
            "percentage": round(exp_weight * 100, 1)
        },
        "education_match": {
            "score": int(round(edu_score)),
            "max": 15,
            "percentage": round(edu_weight * 100, 1)
        },
        "semantic_similarity": {
            "score": int(round(sim_score)),
            "max": 15,
            "percentage": round(similarity * 100, 1)
        },
        "project_relevance": {
            "score": int(round(proj_score)),
            "max": 10,
            "percentage": round(proj_weight * 100, 1)
        },
        "certifications": {
            "score": int(round(cert_score)),
            "max": 5,
            "percentage": round(cert_weight * 100, 1)
        },
        "resume_quality": {
            "score": int(round(quality_score)),
            "max": 5,
            "percentage": round(quality_weight * 100, 1)
        }
    }
    
    return {
        "ats_score": ats_score_int,
        "grade": get_ats_grade(ats_score_int),
        "breakdown": breakdown,
        "missing_skills": skill_match_res.get("missing", []),
        "matched_skills": skill_match_res.get("matched", [])
    }


def predict_ats_score(X: np.ndarray) -> np.ndarray:
    """Prediction function representing the linear combination of the ATS scoring formula."""
    # Weights for: skill_match, experience_match, education_match, semantic_similarity, project_relevance, certifications, resume_quality
    weights = np.array([0.3, 0.2, 0.15, 0.15, 0.1, 0.05, 0.05])
    return np.dot(X, weights)


def explain_score(candidate_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs compute_ats_score and uses SHAP to calculate the impact of each feature
    on the final score, generating human-readable positive/negative breakdowns.
    """
    # 1. Run base scoring
    scoring_res = compute_ats_score(candidate_data, jd_data)
    ats_score = scoring_res["ats_score"]
    breakdown = scoring_res["breakdown"]
    missing_skills = scoring_res["missing_skills"]
    matched_skills = scoring_res["matched_skills"]
    
    candidate_id = candidate_data.get("id")
    job_id = jd_data.get("id")
    if candidate_id and job_id:
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
            from ml import tracking
            tracking.log_ats_score_run(candidate_id, job_id, ats_score, breakdown)
        except Exception as e:
            logger.warning(f"Failed to log ATS score run to MLflow: {e}")
    
    # 2. Extract feature percentages (0-100)
    features_ordered = [
        "skill_match", "experience_match", "education_match",
        "semantic_similarity", "project_relevance", "certifications", "resume_quality"
    ]
    feature_values = np.array([[breakdown[f]["percentage"] for f in features_ordered]])
    
    # 3. Setup SHAP Explainer (Linear combination explainer using a zero reference baseline)
    background = np.zeros((1, 7))
    explainer = shap.Explainer(predict_ats_score, background)
    shap_values = explainer(feature_values)
    
    # Extract the attribution (SHAP) values
    attributions = shap_values.values[0]
    
    top_positives = []
    top_negatives = []
    
    # Display factor metadata and text generation helpers
    cv_text = candidate_data.get("raw_text", "")
    cv_years = candidate_data.get("total_experience_years", 0.0)
    required_years = jd_data.get("required_experience_years")
    cv_edu_section = candidate_data.get("raw_sections", {}).get("education", {}).get("text", "")
    cv_education = extract_education(cv_edu_section or cv_text)
    jd_education = jd_data.get("required_education")
    
    factor_mapping = {
        "skill_match": {
            "name": "Skill match",
            "detail_pos": f"Matched {len(matched_skills)} of {len(matched_skills) + len(missing_skills)} required skills",
            "detail_neg": f"{', '.join(missing_skills[:3])} not found in CV" if missing_skills else "Missing some required skills"
        },
        "experience_match": {
            "name": "Experience",
            "detail_pos": f"{cv_years} years meets the {required_years}-year requirement" if required_years else f"{cv_years} years of experience",
            "detail_neg": f"{cv_years} years is below the required {required_years} years"
        },
        "education_match": {
            "name": "Education",
            "detail_pos": f"{cv_education or 'Bachelor'} degree meets the required education level" if jd_education else "Degree level aligns with criteria",
            "detail_neg": f"{cv_education or 'No'} degree is below the required {jd_education} level"
        },
        "semantic_similarity": {
            "name": "Semantic similarity",
            "detail_pos": "CV content aligns closely with the job description keywords",
            "detail_neg": "CV language could better match job description keywords"
        },
        "project_relevance": {
            "name": "Project relevance",
            "detail_pos": "Projects section shows relevant hands-on experience",
            "detail_neg": "Projects do not show significant semantic overlap with requirements"
        },
        "certifications": {
            "name": "Certifications",
            "detail_pos": "Certifications section aligns with the job profile",
            "detail_neg": "Adding relevant professional certifications would boost match score"
        },
        "resume_quality": {
            "name": "Resume quality",
            "detail_pos": "Resume is complete and well-structured",
            "detail_neg": "Completeness or formatting structure can be improved"
        }
    }
    
    for i, feature in enumerate(features_ordered):
        score_val = breakdown[feature]["score"]
        max_val = breakdown[feature]["max"]
        pct = breakdown[feature]["percentage"]
        attrib = attributions[i]
        
        display_name = factor_mapping[feature]["name"]
        
        # Categorize contributions
        if pct >= 75.0:
            top_positives.append({
                "factor": display_name,
                "impact": f"+{int(round(attrib))} points",
                "detail": factor_mapping[feature]["detail_pos"]
            })
        else:
            lost_points = max_val - score_val
            # Map "Skill match" to "Missing skills" inside negative factor mapping to match user requirements
            neg_factor_name = "Missing skills" if feature == "skill_match" else display_name
            top_negatives.append({
                "factor": neg_factor_name,
                "impact": f"-{int(round(lost_points))} points",
                "detail": factor_mapping[feature]["detail_neg"]
            })
            
    # Sort contributions by absolute impact magnitude
    top_positives.sort(key=lambda x: int(x["impact"].replace("+", "").replace(" points", "")), reverse=True)
    top_negatives.sort(key=lambda x: int(x["impact"].replace("-", "").replace(" points", "")), reverse=True)
    
    # 4. Generate recommendations
    if missing_skills:
        lost_skill_points = breakdown["skill_match"]["max"] - breakdown["skill_match"]["score"]
        recommendation = f"Add {', '.join(missing_skills[:2])} to your skills section to improve your score by ~{int(round(lost_skill_points))} points"
    elif top_negatives:
        worst_neg = top_negatives[0]
        recommendation = f"Improve your {worst_neg['factor'].lower()} (currently costing {worst_neg['impact']}) by adding more descriptive project items or certifications."
    else:
        recommendation = "Your CV is highly optimized for this job description!"
        
    return {
        "ats_score": ats_score,
        "top_positives": top_positives,
        "top_negatives": top_negatives,
        "recommendation": recommendation,
        "breakdown": breakdown,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills
    }
