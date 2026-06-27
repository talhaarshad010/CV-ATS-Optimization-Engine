import re
import spacy
from typing import Dict, List, Any

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

def extract_name_heuristic(text: str) -> str:
    """Helper to extract candidate name from the first two lines of text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    # Check the first two non-empty lines
    for line in lines[:2]:
        # Clean line from punctuation
        clean_line = re.sub(r'[^\w\s]', '', line).strip()
        words = clean_line.split()
        # A candidate name is typically 2 to 4 words, contains only letters, and avoids resume keywords
        if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
            exclude_keywords = {"curriculum", "vitae", "resume", "cv", "page", "contact", "about", "summary", "email", "phone"}
            if not any(w.lower() in exclude_keywords for w in words):
                return line
    return ""

def filter_locations(gpes: List[str]) -> List[str]:
    """Filters out common technical terms or non-location keywords misclassified as locations."""
    exclude_gpe_words = {
        "ai", "ui", "ux", "next.js", "react", "native", "pipelines", "typescript", 
        "javascript", "developer", "engineer", "software", "custom", "api", "apis", 
        "git", "github", "docker", "kubernetes", "aws", "html", "css", "rest", "sql", 
        "nosql", "mongodb", "redux", "firebase", "node", "python", "fastapi", "django", 
        "cicd", "testing", "web", "mobile", "app", "apps", "cloud", "proficient", 
        "competent", "familiar", "bridge", "systems", "integrations", "solutions",
        "fullstack", "frontend", "backend", "ts", "js", "db", "database", "person", "role"
    }
    filtered = []
    for gpe in gpes:
        words = re.findall(r'[a-zA-Z]+', gpe.lower())
        gpe_lower = gpe.lower().strip()
        if any(w in exclude_gpe_words for w in words) or gpe_lower in exclude_gpe_words:
            continue
        if re.search(r'\d', gpe):
            continue
        filtered.append(gpe)
    return filtered

def extract_ner(text: str) -> Dict[str, Any]:
    """
    Extracts named entities from CV text using a hybrid approach:
    - Regex: for high-precision extraction of Email, Phone, and LinkedIn URLs.
    - spaCy (en_core_web_sm): for candidate Name (PERSON), Companies/Universities (ORG),
      Locations (GPE), and Dates/Years (DATE).
      
    If extraction fails or spaCy model is unavailable, returns an empty dictionary.
    """
    if not text or nlp is None:
        return {}

    try:
        doc = nlp(text)
    except Exception:
        return {}

    # 1. Regex High-Precision Extractions
    # Email
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    email_match = email_pattern.search(text)
    email = email_match.group(0) if email_match else ""

    # Phone number (extracts standard phone patterns, filters out year ranges)
    phone_pattern = re.compile(
        r'\+?\b\d{1,4}[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,6}\b'
    )
    phone_matches = phone_pattern.findall(text)
    phone = ""
    for m in phone_matches:
        digits = re.sub(r'\D', '', m)
        # Ensure it has between 7 and 15 digits (valid E.164 lengths)
        if 7 <= len(digits) <= 15:
            # Skip year ranges (e.g. 2020-2023 or 2020 - 2023)
            if re.match(r'^\d{4}\s*-\s*\d{4}$', m.strip()):
                continue
            phone = m.strip()
            break

    # LinkedIn URL
    linkedin_pattern = re.compile(
        r'\b(?:https?://)?(?:www\.)?linkedin\.com/in/[-a-zA-Z0-9_]+/?\b',
        re.IGNORECASE
    )
    linkedin_match = linkedin_pattern.search(text)
    linkedin = linkedin_match.group(0) if linkedin_match else ""
    if linkedin:
        linkedin = linkedin.rstrip("/")

    # 2. spaCy Named Entity Recognition (NER)
    raw_names = []
    raw_orgs = []
    raw_gpes = []
    raw_dates = []

    for ent in doc.ents:
        clean_ent = ent.text.strip()
        if not clean_ent or len(clean_ent) < 2:
            continue
            
        # Prevent entities from spanning multiple lines (e.g. "John Doe\nEmail")
        clean_ent = clean_ent.split("\n")[0].strip()
        if not clean_ent or len(clean_ent) < 2:
            continue

        if ent.label_ == "PERSON":
            raw_names.append(clean_ent)
        elif ent.label_ == "ORG":
            raw_orgs.append(clean_ent)
        elif ent.label_ == "GPE":
            raw_gpes.append(clean_ent)
        elif ent.label_ == "DATE":
            raw_dates.append(clean_ent)

    # De-duplicate lists while preserving order
    def deduplicate(lst: List[str]) -> List[str]:
        seen = set()
        result = []
        for x in lst:
            norm = x.lower()
            if norm not in seen:
                seen.add(norm)
                result.append(x)
        return result

    organizations = deduplicate(raw_orgs)
    dates = deduplicate(raw_dates)
    unique_gpes = filter_locations(deduplicate(raw_gpes))

    # Candidate Name (heuristic first, fallback to first PERSON entity found in the header)
    name = extract_name_heuristic(text)
    if not name:
        name = deduplicate(raw_names)[0] if raw_names else ""
    
    # Location (join GPEs like "Munich, Germany")
    location = ", ".join(unique_gpes) if unique_gpes else ""

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "location": location,
        "organizations": organizations,
        "dates": dates
    }
