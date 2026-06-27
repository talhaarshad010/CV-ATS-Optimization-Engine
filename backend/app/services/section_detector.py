import re
from typing import Dict

# Regex patterns for identifying common CV section headers
SECTION_PATTERNS = {
    "summary": r"^#*\s*(?:professional\s+|career\s+|personal\s+)?(?:summary|objective|profile|about(?:\s+me)?)\b\s*[:\-#]*$",
    "education": r"^#*\s*(?:education|academic(?:\s+background|\s+history)?|qualifications|academic\s+record)\b\s*[:\-#]*$",
    "experience": r"^#*\s*(?:work\s+|professional\s+|employment\s+|career\s+)?(?:experience|history|background|records|employment)\b\s*[:\-#]*$",
    "skills": r"^#*\s*(?:technical\s+|key\s+|core\s+)?(?:skills|competencies|expertise|technologies|tools|abilities)\b\s*[:\-#]*$",
    "projects": r"^#*\s*(?:personal\s+|academic\s+|selected\s+)?projects\b\s*[:\-#]*$",
    "certifications": r"^#*\s*(?:certifications|licenses|courses|credentials|accreditations)\b\s*[:\-#]*$",
    "languages": r"^#*\s*languages\b\s*[:\-#]*$",
    "achievements": r"^#*\s*(?:awards|honors|achievements|accomplishments|fellowships)\b\s*[:\-#]*$",
}

def detect_sections(text: str) -> Dict[str, Dict[str, str]]:
    """
    Detects and splits a CV text into standard sections using regex header matching.
    
    Stage 1: Header splitting
    - Scans text line-by-line to match section header keywords.
    - Text before the first matched header is mapped to 'personal_info'.
    - Splits remaining text block into respective sections.
    
    Stage 2: Confidence scoring
    - If a section's cleaned content has < 20 characters, its confidence is 'low'.
    - Otherwise, confidence is 'high'.
    
    Returns a dictionary of:
    {
        "section_name": {
            "text": "section content...",
            "confidence": "high" | "low"
        }
    }
    """
    lines = text.splitlines()
    header_indices = []

    # Stage 1: Detect lines that act as section headers
    for idx, line in enumerate(lines):
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # Match each line against the pre-defined section regexes
        for sec_name, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, clean_line, re.IGNORECASE):
                header_indices.append((idx, sec_name))
                break  # Stop checking other patterns for this line

    # Initialize empty section text dictionary
    detected_sections = {
        "personal_info": "",
        "summary": "",
        "education": "",
        "experience": "",
        "skills": "",
        "projects": "",
        "certifications": "",
        "languages": "",
        "achievements": ""
    }

    if not header_indices:
        # If no headers detected, attribute the entire text to personal_info
        detected_sections["personal_info"] = text.strip()
    else:
        # Anything before the first detected header is considered personal_info
        first_header_idx = header_indices[0][0]
        detected_sections["personal_info"] = "\n".join(lines[:first_header_idx]).strip()

        # Extract content for each detected section
        for i in range(len(header_indices)):
            start_line_idx, sec_name = header_indices[i]

            # The section content goes until the next matched header, or the end of the text
            if i + 1 < len(header_indices):
                end_line_idx = header_indices[i + 1][0]
            else:
                end_line_idx = len(lines)

            # Join lines (skipping the header line itself)
            content = "\n".join(lines[start_line_idx + 1:end_line_idx]).strip()

            # Append content if a section type appears multiple times
            if detected_sections[sec_name]:
                detected_sections[sec_name] += "\n\n" + content
            else:
                detected_sections[sec_name] = content

    # Stage 2: Calculate confidence scores based on text length
    result = {}
    for sec_name, sec_text in detected_sections.items():
        cleaned_text = sec_text.strip()
        
        # Determine confidence score
        if len(cleaned_text) < 20:
            confidence = "low"
        else:
            confidence = "high"
            
        result[sec_name] = {
            "text": cleaned_text,
            "confidence": confidence
        }

    return result
