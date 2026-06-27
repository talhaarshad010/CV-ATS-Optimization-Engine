import logging
import re
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Cached pipeline instance
_nlp_pipeline = None

def get_pipeline():
    """
    Initializes and caches the Hugging Face BERT NER pipeline.
    Uses 'dslim/bert-base-NER' with aggregation_strategy='simple'
    to automatically group B- and I- tokens into complete word spans.
    """
    global _nlp_pipeline
    if _nlp_pipeline is None:
        try:
            from transformers import pipeline
            _nlp_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
        except Exception as e:
            logger.warning(f"Failed to load Hugging Face BERT NER pipeline: {e}")
            _nlp_pipeline = None
    return _nlp_pipeline

def extract_ner_bert(text: str) -> Dict[str, Any]:
    """
    Extracts named entities from text using BERT (fallback for spaCy).
    
    Returns:
    {
      "name": "Candidate Name (first PER entity found)",
      "organizations": ["List of unique ORGs"],
      "locations": ["List of unique LOCs"],
      "raw_entities": [{"text": "entity text", "label": "PER|ORG|LOC|MISC"}]
    }
    """
    if not text:
        return {}

    pipeline = get_pipeline()
    if pipeline is None:
        return {}

    try:
        entities = pipeline(text)
    except Exception as e:
        logger.warning(f"BERT NER inference failed: {e}")
        return {}

    raw_entities = []
    names = []
    organizations = []
    locations = []

    for ent in entities:
        label = ent.get("entity_group", "")
        word = ent.get("word", "").strip()

        # Ignore empty/too short extractions
        if not word or len(word) < 2:
            continue

        raw_entities.append({
            "text": word,
            "label": label
        })

        if label == "PER":
            names.append(word)
        elif label == "ORG":
            organizations.append(word)
        elif label == "LOC":
            locations.append(word)

    # De-duplicate lists preserving order
    def deduplicate(lst: List[str]) -> List[str]:
        seen = set()
        result = []
        for x in lst:
            norm = x.lower()
            if norm not in seen:
                seen.add(norm)
                result.append(x)
        return result

    organizations = deduplicate(organizations)
    from app.services.ner_spacy import filter_locations
    locations = filter_locations(deduplicate(locations))
    unique_names = deduplicate(names)

    # Name is the first PERSON entity found (or extracted by heuristic)
    from app.services.ner_spacy import extract_name_heuristic
    name = extract_name_heuristic(text)
    if not name:
        name = unique_names[0] if unique_names else ""

    return {
        "name": name,
        "organizations": organizations,
        "locations": locations,
        "raw_entities": raw_entities
    }
