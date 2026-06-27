import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from app.services.section_detector import detect_sections
from app.services.skill_normalizer import normalize_skills
from app.services.skill_ontology import _lookup_dict
from app.services.ner_spacy import nlp

logger = logging.getLogger(__name__)

# Ensure SpaCy is loaded
_nlp = nlp
if _nlp is None:
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.error(f"Failed to load SpaCy model for JD parser: {e}")


def extract_job_title(text: str) -> str:
    """Extracts job title from the first few lines of the text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Unknown Job Title"
        
    title_indicators = [
        "developer", "engineer", "designer", "manager", "analyst", "specialist", 
        "architect", "lead", "senior", "junior", "intern", "associate", "consultant", 
        "director", "coordinator", "administrator", "scientist", "programmer"
    ]
    
    # Check the first 4 lines
    for line in lines[:4]:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in title_indicators):
            # Clean up markdown headers if present
            cleaned_line = re.sub(r'^#+\s*', '', line).strip()
            return cleaned_line
            
    # Fallback to the first non-empty line
    return re.sub(r'^#+\s*', '', lines[0]).strip()


def extract_experience_years(text: str) -> Optional[int]:
    """Extracts the minimum years of experience using regex."""
    patterns = [
        r'\b(\d+)\+?\s*(?:-\s*\d+\+?\s*)?years?\s+(?:of\s+)?experience\b',
        r'\bminimum\s+(?:of\s+)?(\d+)\s*years?\b',
        r'\bat\s+least\s+(\d+)\s*years?\b',
        r'\b(\d+)\s*years?\s+required\b',
        r'\b(\d+)\s*years?\s+minimum\b',
    ]
    
    years_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            try:
                years_found.append(int(m))
            except ValueError:
                pass
                
    if years_found:
        return min(years_found)
    return None


def extract_education(text: str) -> Optional[str]:
    """Extracts the required education degree level mentioned."""
    text_lower = text.lower()
    
    phd_keywords = ["phd", "ph.d.", "doctorate", "doctor of philosophy"]
    master_keywords = ["master's", "masters", "master of", "m.s.", "m.sc.", "msc", "ms degree", "mba"]
    bachelor_keywords = ["bachelor's", "bachelors", "bachelor of", "b.s.", "b.sc.", "bsc", "bs degree", "ba degree", "b.a.", "undergraduate degree", "college degree", "university degree"]
    
    if any(k in text_lower for k in bachelor_keywords):
        return "Bachelor"
    if any(k in text_lower for k in master_keywords):
        return "Master"
    if any(k in text_lower for k in phd_keywords):
        return "PhD"
        
    if "degree" in text_lower:
        return "Bachelor"
        
    return None


def extract_responsibilities(text: str) -> List[str]:
    """Extracts a list of key responsibilities (bullet points)."""
    responsibilities = []
    lines = text.splitlines()
    
    resp_headers = ["responsibilities", "duties", "what you will do", "the role", "key responsibilities", "your impact", "what you'll do", "about the role"]
    other_headers = ["requirements", "skills", "qualifications", "what you need", "who you are", "about you", "nice to have", "education", "experience"]
    
    in_resp_section = False
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        line_lower = line_strip.lower()
        
        # Check if this line is a section header
        if len(line_strip) < 50:
            if any(h in line_lower for h in resp_headers):
                in_resp_section = True
                continue
            elif any(h in line_lower for h in other_headers):
                in_resp_section = False
                continue
                
        if in_resp_section:
            # Check if it looks like a list item / bullet point
            if re.match(r'^[-\*\+\s•‣◦▪▫\d+\.)]+', line_strip):
                cleaned = re.sub(r'^[-\*\+\s•‣◦▪▫\d+\.)]+', '', line_strip).strip()
                if cleaned:
                    responsibilities.append(cleaned)
            elif len(line_strip) > 30 and not line_strip.endswith(('.', ':', '?')):
                responsibilities.append(line_strip)
                
    # Fallback to any bullet points with action verbs if responsibilities section was not found/empty
    if not responsibilities:
        action_verbs = ["build", "develop", "create", "manage", "lead", "write", "work", "design", "implement", "collaborate", "support", "maintain", "drive", "deliver"]
        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue
            if re.match(r'^[-\*\+•‣◦▪▫]+', line_strip):
                cleaned = re.sub(r'^[-\*\+•‣◦▪▫]+', '', line_strip).strip()
                line_lower = cleaned.lower()
                if any(line_lower.startswith(v) for v in action_verbs):
                    responsibilities.append(cleaned)
                    
    return responsibilities[:10]


def extract_jd_skills(text: str) -> Tuple[List[str], List[str]]:
    """Extracts, normalizes, and groups skills into required and preferred lists."""
    current_context = "required"
    required_raw = []
    preferred_raw = []
    
    lines = text.splitlines()
    
    pref_headers = ["preferred", "nice to have", "plus", "bonus", "desirable", "desired", "optional", "advantage", "highly regarded"]
    req_headers = ["required", "minimum", "requirements", "must have", "key qualifications", "essential"]
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        line_lower = line_strip.lower()
        
        # Check for context change in headers
        if len(line_strip) < 50:
            if any(h in line_lower for h in pref_headers):
                current_context = "preferred"
                continue
            elif any(h in line_lower for h in req_headers):
                current_context = "required"
                continue
                
        # Extract skills from line using exact ontology match
        tokens = [t.strip() for t in re.split(r'[,;\n•|]', line_strip) if t.strip()]
        line_skills = []
        for token in tokens:
            token_clean = re.sub(r'^[-\*\+\s•]+', '', token).strip()
            token_clean = re.sub(r'[-\*\s]+$', '', token_clean).strip()
            if token_clean.lower() in _lookup_dict:
                line_skills.append(token_clean)
                
        # Extract noun chunks using SpaCy
        if _nlp is not None:
            try:
                doc = _nlp(line_strip)
                for chunk in doc.noun_chunks:
                    chunk_clean = chunk.text.strip()
                    chunk_clean = " ".join(chunk_clean.split())
                    chunk_clean = re.sub(r'^[-\*\+\s•]+', '', chunk_clean).strip()
                    if chunk_clean.lower() in _lookup_dict:
                        line_skills.append(chunk_clean)
            except Exception:
                pass
                
        # Deduplicate line level skills
        line_skills = list(set(line_skills))
        
        # Override context if line specifically mentions preferred/required words
        is_pref_line = (current_context == "preferred" or any(h in line_lower for h in pref_headers))
        
        if is_pref_line:
            preferred_raw.extend(line_skills)
        else:
            required_raw.extend(line_skills)
            
    # Clean, normalize, and sort
    def clean_dedup_and_normalize(raw_list: List[str]) -> List[str]:
        seen = set()
        dedup = []
        for s in raw_list:
            kl = s.lower()
            if kl not in seen:
                seen.add(kl)
                dedup.append(s)
        
        normalized_res = normalize_skills(dedup)
        return sorted(list(set(item["normalized"] for item in normalized_res if item.get("normalized"))))

    req_normalized = clean_dedup_and_normalize(required_raw)
    pref_normalized = clean_dedup_and_normalize(preferred_raw)
    
    # Ensure preferred skills don't overlap with required skills
    pref_normalized = [s for s in pref_normalized if s not in req_normalized]
    
    return req_normalized, pref_normalized


def parse_jd(raw_text: str) -> Dict[str, Any]:
    """Parses a Job Description (JD) text and returns structured fields."""
    if not raw_text:
        return {
            "job_title": "Unknown Job Title",
            "required_skills": [],
            "preferred_skills": [],
            "required_experience_years": None,
            "required_education": None,
            "responsibilities": []
        }
        
    job_title = extract_job_title(raw_text)
    required_exp = extract_experience_years(raw_text)
    required_edu = extract_education(raw_text)
    responsibilities = extract_responsibilities(raw_text)
    
    req_skills, pref_skills = extract_jd_skills(raw_text)
    
    return {
        "job_title": job_title,
        "required_skills": req_skills,
        "preferred_skills": pref_skills,
        "required_experience_years": required_exp,
        "required_education": required_edu,
        "responsibilities": responsibilities
    }
