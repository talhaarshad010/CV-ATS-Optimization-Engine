import re
import logging
from typing import Dict, Any, List

from app.utils.ollama_client import generate

logger = logging.getLogger(__name__)


def split_into_bullets(text: str) -> List[str]:
    """Splits a raw experience text block into individual cleaned bullet points."""
    if not text:
        return []
        
    lines = text.splitlines()
    bullets = []
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        # Strip common leading bullet marks or lists (e.g. *, -, •, 1.)
        cleaned = re.sub(r'^[-\*\+\s•‣◦▪▫\d+\.)]+', '', line_strip).strip()
        if cleaned:
            bullets.append(cleaned)
            
    return bullets


def rewrite_bullet_points(experience_text: str, job_title: str) -> Dict[str, Any]:
    """
    Splits experience text into bullet points and rewrites each using local Llama 3.
    """
    original_bullets = split_into_bullets(experience_text)
    rewritten_bullets = []

    system_prompt = (
        "You are an expert resume writer. Rewrite the given resume bullet point to be more impactful. "
        "Use action verbs. Add metrics if possible. Keep it under 20 words. Return only the rewritten bullet, nothing else."
    )

    for bullet in original_bullets:
        user_prompt = f"Rewrite this bullet point for a {job_title} role: {bullet}"
        try:
            rewritten = generate(prompt=user_prompt, system=system_prompt, temperature=0.4)
            rewritten_clean = rewritten.strip().replace('"', '')  # Remove any LLM wrapping quotes
            rewritten_bullets.append(rewritten_clean)
        except Exception as e:
            logger.error(f"Failed to rewrite bullet '{bullet}': {e}")
            # Fallback to original bullet in case of error
            rewritten_bullets.append(bullet)

    return {
        "original_bullets": original_bullets,
        "rewritten_bullets": rewritten_bullets,
        "improvement_count": len(rewritten_bullets)
    }


def improve_summary(summary_text: str, job_title: str, top_skills: List[str]) -> str:
    """
    Rewrites a CV summary targeting a job title and incorporating top skills naturally.
    """
    if not summary_text:
        return ""

    system_prompt = (
        "You are an expert resume writer. Rewrite the given resume summary to target the specified job title "
        "and naturally incorporate the listed key skills. Keep it professional, compelling, and limited to 2-3 sentences max. "
        "Return only the rewritten summary, nothing else."
    )

    skills_str = ", ".join(top_skills) if top_skills else "relevant technical skills"
    user_prompt = (
        f"Rewrite this summary targeting a {job_title} role. "
        f"Incorporate these key skills: {skills_str}. "
        f"Original summary: {summary_text}"
    )

    try:
        improved = generate(prompt=user_prompt, system=system_prompt, temperature=0.4)
        return improved.strip().replace('"', '')
    except Exception as e:
        logger.error(f"Failed to improve summary: {e}")
        return summary_text
