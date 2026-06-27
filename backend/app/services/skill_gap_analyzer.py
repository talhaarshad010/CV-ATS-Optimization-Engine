import json
import re
import logging
from typing import Dict, Any, List

from app.utils.ollama_client import generate

logger = logging.getLogger(__name__)


def extract_json_array(text: str) -> List[Dict[str, Any]]:
    """Robust helper to find and parse a JSON array inside LLM output."""
    text_strip = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text_strip)
    except json.JSONDecodeError:
        pass
        
    # Extract the block between the first '[' and the last ']'
    start_idx = text_strip.find("[")
    end_idx = text_strip.rfind("]")
    if start_idx != -1 and end_idx != -1:
        json_str = text_strip[start_idx:end_idx + 1]
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode extracted JSON block: {e}")
            
    raise ValueError("No valid JSON array found in LLM output.")


def analyze_gaps(missing_skills: List[str], candidate_skills: List[str], job_title: str) -> Dict[str, Any]:
    """
    Queries local Llama 3 to analyze missing skills, recommending learning resources
    and projects for each. Includes a retry mechanism for robust JSON outputs.
    """
    if not missing_skills:
        return {
            "gaps": [],
            "total_gaps": 0,
            "estimated_total_weeks": 0
        }

    system_prompt = (
        "You are a career advisor. Given missing skills for a job role, suggest how to learn them. "
        "Be specific and practical. Return ONLY a valid JSON array matching the requested schema. "
        "Do not include any intro, markdown block backticks (like ```json), conversational text, or explanation."
    )

    user_prompt = (
        f"Job: {job_title}.\n"
        f"Missing skills: {missing_skills}.\n"
        f"Current skills: {candidate_skills}.\n\n"
        "For each missing skill, suggest a learning path. Return a JSON array of objects, where each object has exactly these keys:\n"
        '- "skill": (string, name of the skill)\n'
        '- "priority": (string, one of: "high", "medium", "low")\n'
        '- "suggested_course": (string, 1 specific free online course or YouTube channel/video)\n'
        '- "suggested_project": (string, 1 specific hands-on project to build)\n'
        '- "estimated_weeks": (integer, estimated learning time in weeks)\n'
    )

    # First attempt
    try:
        response = generate(prompt=user_prompt, system=system_prompt, temperature=0.3)
        gaps_list = extract_json_array(response)
    except Exception as e:
        logger.warning(f"First attempt to analyze skill gaps failed: {e}. Retrying once...")
        
        # Retry with clearer formatting instructions
        retry_system_prompt = (
            "You are a strict JSON generator. Given missing skills, output ONLY a valid JSON array of objects. "
            "Do not include any surrounding text, conversational intros, or code block backticks. "
            "Example response format: [{\"skill\": \"Docker\", \"priority\": \"high\", \"suggested_course\": \"Docker Tutorial on YouTube\", \"suggested_project\": \"Containerize an API\", \"estimated_weeks\": 2}]"
        )
        try:
            response = generate(prompt=user_prompt, system=retry_system_prompt, temperature=0.2)
            gaps_list = extract_json_array(response)
        except Exception as retry_err:
            logger.error(f"Ollama skill gap retry failed: {retry_err}. Using fallback response.")
            
            # Safe fallback so the application does not crash
            gaps_list = [
                {
                    "skill": skill,
                    "priority": "high",
                    "suggested_course": f"Learn {skill} on YouTube or freeCodeCamp",
                    "suggested_project": f"Build a prototype project utilizing {skill}",
                    "estimated_weeks": 2
                }
                for skill in missing_skills
            ]

    # Calculate statistics
    total_gaps = len(gaps_list)
    estimated_total_weeks = sum(int(item.get("estimated_weeks", 2)) for item in gaps_list)

    return {
        "gaps": gaps_list,
        "total_gaps": total_gaps,
        "estimated_total_weeks": estimated_total_weeks
    }


def generate_improvement_plan(ats_score: int, breakdown: Dict[str, Any], gaps: Dict[str, Any]) -> str:
    """
    Generates a targeted 5-step plain-text improvement plan using local Llama 3.
    """
    system_prompt = (
        "You are an expert resume writer and career coach. Write a concise, actionable, 5-step improvement plan "
        "to increase the candidate's ATS score based on their score, score breakdown, and skill gaps. "
        "Keep it to 5 numbered steps, professional, and highly practical. Return ONLY the plan, nothing else."
    )

    gaps_str = json.dumps(gaps.get("gaps", []), indent=2)
    breakdown_str = json.dumps(breakdown, indent=2)
    
    user_prompt = (
        f"ATS Score: {ats_score}/100\n"
        f"Breakdown: {breakdown_str}\n"
        f"Identified Gaps: {gaps_str}\n\n"
        "Generate the 5-step improvement plan."
    )

    try:
        plan = generate(prompt=user_prompt, system=system_prompt, temperature=0.3)
        return plan.strip()
    except Exception as e:
        logger.error(f"Failed to generate improvement plan: {e}", exc_info=True)
        return (
            "1. Add the missing required skills to your resume skills section.\n"
            "2. Showcase these skills inside your experience descriptions using action verbs.\n"
            "3. Revise your project descriptions to align with the job description keywords.\n"
            "4. Obtain relevant professional certifications mentioned in the job description.\n"
            "5. Refine resume structure and spacing to optimize layout and section clarity."
        )
