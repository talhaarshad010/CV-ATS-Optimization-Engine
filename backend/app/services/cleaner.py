import re
import unicodedata
from typing import Dict

def clean_text(text: str) -> Dict[str, str]:
    """
    Cleans raw extracted text from a CV:
    - Normalizes unicode characters (collapses smart quotes, dashes, ligatures).
    - Removes extra whitespace and empty/blank lines.
    - Strips non-printable control characters.
    - Returns a dictionary with:
      - 'display_text': Cleaned text preserving original casing.
      - 'cleaned_text': Lowercased version for NLP processing.
    """
    if not text:
        return {"cleaned_text": "", "display_text": ""}

    # 1. Normalize unicode characters (accents, ligatures, compatibility characters)
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Map specific unicode smart quotes/dashes to standard ascii counterparts
    unicode_map = {
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2022": "*",  # Bullet point symbol
    }
    for char, replacement in unicode_map.items():
        normalized = normalized.replace(char, replacement)

    # 3. Clean line by line to remove extra whitespaces and empty lines
    cleaned_lines = []
    for line in normalized.splitlines():
        # Remove leading/trailing whitespace
        stripped = line.strip()
        if not stripped:
            continue

        # Collapse multiple spaces within a line
        collapsed = re.sub(r"\s+", " ", stripped)

        # Remove control characters (Unicode category 'C')
        printable_line = "".join(
            char for char in collapsed if not unicodedata.category(char).startswith("C")
        )

        if printable_line:
            cleaned_lines.append(printable_line)

    # Reconstruct cleaned display text
    display_text = "\n".join(cleaned_lines)

    # Lowercase version for NLP processing
    cleaned_text = display_text.lower()

    return {
        "cleaned_text": cleaned_text,
        "display_text": display_text
    }
