import logging
import re
from typing import List, Dict, Any

from app.services.ner_spacy import nlp
from app.services.skill_ontology import _lookup_dict
from app.services.skill_normalizer import normalize_skills, get_normalizer
from app.utils.supabase_client import insert_skills

logger = logging.getLogger(__name__)

# Ensure SpaCy is loaded
_nlp = nlp
if _nlp is None:
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.error(f"Failed to load SpaCy model for skill extractor: {e}")

def extract_skills_from_cv(sections: Dict[str, Any], candidate_id: str = None) -> Dict[str, Any]:
    """
    Extracts, deduplicates, and normalizes skills from a candidate's CV sections.
    Saves the extracted skills to Supabase if candidate_id is provided.
    """
    skills_from_section = []
    skills_from_experience = []
    
    # 1. Source A — Skills section
    skills_sec = sections.get("skills", {})
    skills_text = skills_sec.get("text", "") if isinstance(skills_sec, dict) else ""
    if skills_text:
        # Reuse the clean_raw_skills helper from SkillNormalizer to clean/split
        try:
            normalizer = get_normalizer()
            skills_from_section = normalizer.clean_raw_skills(skills_text)
        except Exception as e:
            logger.error(f"Error splitting skills section: {e}")
            # Basic fallback split in case clean_raw_skills fails
            skills_from_section = [s.strip() for s in re.split(r'[,;\n•|]', skills_text) if s.strip()]
            
    # 2. Source B — Experience section (SpaCy noun chunks matching known ontology skills)
    experience_sec = sections.get("experience", {})
    experience_text = experience_sec.get("text", "") if isinstance(experience_sec, dict) else ""
    if experience_text and _nlp is not None:
        try:
            doc = _nlp(experience_text)
            for chunk in doc.noun_chunks:
                chunk_clean = chunk.text.strip()
                # Collapse extra spaces
                chunk_clean = " ".join(chunk_clean.split())
                # Remove common leading bullet or list characters if present in noun phrase
                chunk_clean = re.sub(r'^[-\*\+\s•]+', '', chunk_clean).strip()
                
                if not chunk_clean:
                    continue
                
                chunk_lower = chunk_clean.lower()
                # Match against ESCO ontology lookup dictionary keys
                if chunk_lower in _lookup_dict:
                    skills_from_experience.append(chunk_clean)
        except Exception as e:
            logger.error(f"Error extracting noun chunks from experience section: {e}")
            
    # 3. Deduplicate (case-insensitive merge)
    seen = set()
    deduplicated_skills = []
    for skill in skills_from_section + skills_from_experience:
        norm_key = skill.strip().lower()
        if norm_key and norm_key not in seen:
            seen.add(norm_key)
            deduplicated_skills.append(skill.strip())
            
    # 4. Pass the full list to skill_normalizer.normalize_skills()
    logger.info(f"Normalizing {len(deduplicated_skills)} unique raw skills...")
    normalized_results = normalize_skills(deduplicated_skills)
    
    # 5. Calculate statistics
    high_confidence = sum(1 for s in normalized_results if s["confidence"] >= 0.75)
    low_confidence = sum(1 for s in normalized_results if s["confidence"] < 0.75)
    
    response = {
        "skills": normalized_results,
        "total_found": len(normalized_results),
        "high_confidence": high_confidence,
        "low_confidence": low_confidence
    }
    
    # 6. Save to Supabase if candidate_id is provided
    if candidate_id:
        logger.info(f"Saving {len(normalized_results)} skills to database for candidate {candidate_id}...")
        try:
            insert_skills(candidate_id, normalized_results)
        except Exception as e:
            logger.error(f"Failed to save extracted skills to Supabase for candidate {candidate_id}: {e}", exc_info=True)
            
    return response
