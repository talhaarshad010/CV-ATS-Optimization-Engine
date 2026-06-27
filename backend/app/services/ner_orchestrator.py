import re
import logging
from datetime import datetime
from dateutil import parser
from typing import Dict, Any, List

from app.services.ner_spacy import extract_ner as extract_spacy
from app.services.ner_bert import extract_ner_bert as extract_bert

logger = logging.getLogger(__name__)

# Regex for extracting date ranges from experience section
DATE_RANGE_PATTERN = re.compile(
    r'\b(?:'
    r'([a-zA-Z]{3,9}\s+\d{4}|\d{1,2}/\d{2,4}|\d{4})'  # Start date (e.g. Jan 2020, 01/2020, 2020)
    r'\s*(?:-|to|–|—)\s*'                             # Separator (dashes or 'to')
    r'([a-zA-Z]{3,9}\s+\d{4}|\d{1,2}/\d{2,4}|\d{4}|present|current|now)' # End date / Present
    r')\b',
    re.IGNORECASE
)

def parse_date_string(date_str: str, default_year: int = 2026) -> datetime:
    """Parses a date string using dateutil, defaulting to current time for 'present'."""
    clean_str = date_str.strip().lower()
    if clean_str in ["present", "current", "now"]:
        return datetime.now()
        
    try:
        # Use a template default so year-only inputs (like '2020') resolve to Jan 1st of that year
        return parser.parse(date_str, default=datetime(default_year, 1, 1))
    except Exception:
        return None

def calculate_duration_years(start_dt: datetime, end_dt: datetime, start_str: str, end_str: str) -> float:
    """Calculates experience duration in years from start to end datetime."""
    if not start_dt or not end_dt or end_dt < start_dt:
        return 0.0

    # Determine if month information is present in either string (letters or slash format like MM/YYYY)
    has_month = re.search(r'[a-zA-Z]|\b\d{1,2}/', start_str) or re.search(r'[a-zA-Z]|\b\d{1,2}/', end_str)

    if has_month:
        # Calculate month difference and add 1 month to include the starting/ending months in full
        months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
        return round(months / 12.0, 1)
    else:
        # Simple year-only difference (e.g. 2020 to 2023 -> 3 years)
        return float(end_dt.year - start_dt.year)

def extract_experience_years(experience_text: str) -> float:
    """Scans experience text to extract and sum all experience year durations."""
    if not experience_text:
        return 0.0

    matches = DATE_RANGE_PATTERN.findall(experience_text)
    total_years = 0.0

    for start_str, end_str in matches:
        start_dt = parse_date_string(start_str)
        end_dt = parse_date_string(end_str)

        if start_dt and end_dt:
            duration = calculate_duration_years(start_dt, end_dt, start_str, end_str)
            # Avoid abnormally large durations (e.g. bad parses > 50 years)
            if 0.0 < duration < 50.0:
                total_years += duration

    return round(total_years, 1)

def orchestrate_ner(personal_info_text: str, experience_text: str) -> Dict[str, Any]:
    """
    Orchestrates the NER pipeline:
    1. Runs SpaCy NER on personal_info_text first.
    2. Checks if 'name' and 'email' are present.
    3. If either is missing, triggers BERT NER as a fallback and merges the results.
    4. Extracts experience duration from experience_text using python-dateutil.
    5. Returns the final merged candidate profile.
    """
    # Step 1: Run SpaCy NER
    spacy_res = extract_spacy(personal_info_text)
    
    name = spacy_res.get("name", "")
    email = spacy_res.get("email", "")
    
    # Step 2 & 3: Fallback check and merge
    if name and email:
        ner_method = "spacy"
        phone = spacy_res.get("phone", "")
        linkedin = spacy_res.get("linkedin", "")
        location = spacy_res.get("location", "")
    else:
        # Fallback to BERT
        bert_res = extract_bert(personal_info_text)
        ner_method = "spacy+bert"
        
        # Prefer non-empty values
        name = name or bert_res.get("name", "")
        email = email or bert_res.get("email", "")
        phone = spacy_res.get("phone", "") or bert_res.get("phone", "") # Note: bert doesn't extract phone, but good to have fallback
        linkedin = spacy_res.get("linkedin", "") or bert_res.get("linkedin", "")
        
        # Merge locations
        spacy_locations = [x.strip() for x in spacy_res.get("location", "").split(",") if x.strip()]
        bert_locations = bert_res.get("locations", [])
        
        seen = set()
        merged_locations = []
        for loc in spacy_locations + bert_locations:
            norm = loc.lower()
            if norm not in seen:
                seen.add(norm)
                merged_locations.append(loc)
                
        location = ", ".join(merged_locations)

    # Step 4: Experience extraction (fallback to personal_info_text if experience_text yields 0)
    total_exp_years = extract_experience_years(experience_text)
    if total_exp_years == 0.0 and personal_info_text:
        total_exp_years = extract_experience_years(personal_info_text)

    # Step 5: Format response
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "location": location,
        "total_experience_years": total_exp_years,
        "ner_method": ner_method
    }

def orchestrate_cv(sections: Dict[str, Dict[str, str]], candidate_id: str = None) -> Dict[str, Any]:
    """Helper that accepts the full sections dictionary and orchestrates NER."""
    import time
    start_time = time.time()
    
    personal_info_text = sections.get("personal_info", {}).get("text", "")
    experience_text = sections.get("experience", {}).get("text", "")
    
    res = orchestrate_ner(personal_info_text, experience_text)
    
    duration = time.time() - start_time
    if candidate_id:
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
            from ml import tracking
            
            # Identify successfully populated fields
            fields_found = [k for k, v in res.items() if v]
            tracking.log_ner_run(candidate_id, res.get("ner_method", "spacy"), fields_found, duration)
        except Exception as e:
            logger.warning(f"Failed to log NER run to MLflow: {e}")
            
    return res
