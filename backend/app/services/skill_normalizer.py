import os
import re
import logging
import torch
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer, util
from rapidfuzz import process, utils

from app.services import skill_ontology

logger = logging.getLogger(__name__)

class SkillNormalizer:
    def __init__(
        self,
        cache_path: str = "/Users/muhammadtalhaarshad/Downloads/cv-platform/ml/data/esco_skills_embeddings.pt",
        model_name: str = "all-MiniLM-L6-v2",
        semantic_threshold: float = 0.75
    ):
        self.cache_path = cache_path
        self.semantic_threshold = semantic_threshold
        
        logger.info(f"Initializing SkillNormalizer with model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        self.canonical_skills = skill_ontology.get_all_canonical_skills()
        self.canonical_skills_lower = {s.lower() for s in self.canonical_skills}
        self.esco_embeddings = None
        
        self._load_or_generate_embeddings()

    def _load_or_generate_embeddings(self):
        if not self.canonical_skills:
            logger.warning("No canonical skills found in ontology. Embedding cache skipped.")
            return
            
        if os.path.exists(self.cache_path):
            logger.info(f"Loading ESCO embeddings from cache: {self.cache_path}")
            try:
                # Load to CPU first, then transfer to model's device
                loaded = torch.load(self.cache_path, map_location="cpu")
                # Safety check: ensure size matches current canonical skills list
                if loaded.shape[0] == len(self.canonical_skills):
                    self.esco_embeddings = loaded.to(self.model.device)
                    logger.info("Successfully loaded matching ESCO embeddings from cache.")
                    return
                else:
                    logger.warning(f"Cache size mismatch ({loaded.shape[0]} vs {len(self.canonical_skills)}). Recomputing...")
            except Exception as e:
                logger.warning(f"Failed to load cached embeddings: {e}. Recomputing...")
                
        logger.info(f"Computing embeddings for {len(self.canonical_skills)} canonical skills. This will take 1-2 minutes...")
        try:
            embeddings = self.model.encode(self.canonical_skills, convert_to_tensor=True, show_progress_bar=True)
            torch.save(embeddings, self.cache_path)
            self.esco_embeddings = embeddings
            logger.info(f"Successfully computed and cached ESCO embeddings at {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to compute and cache ESCO embeddings: {e}", exc_info=True)

    def normalize_single_skill(self, raw_skill: str) -> Dict[str, Any]:
        raw_clean = raw_skill.strip()
        if not raw_clean:
            return {"raw": raw_skill, "normalized": "", "confidence": 0.0, "method": "unknown"}
            
        raw_lower = raw_clean.lower()
        
        # Stage 1 — Exact match (from ESCO ontology)
        # Check if already canonical
        if raw_lower in self.canonical_skills_lower:
            canonical = skill_ontology.normalize_skill(raw_clean)
            return {
                "raw": raw_skill,
                "normalized": canonical,
                "confidence": 1.0,
                "method": "ontology"
            }
            
        # Check if maps to preferred label
        canonical = skill_ontology.normalize_skill(raw_clean)
        if canonical.lower() != raw_lower:
            return {
                "raw": raw_skill,
                "normalized": canonical,
                "confidence": 1.0,
                "method": "ontology"
            }
            
        # Stage 2 — Fuzzy match (RapidFuzz)
        try:
            match = process.extractOne(
                raw_clean,
                self.canonical_skills,
                processor=utils.default_process,
                score_cutoff=80.0
            )
            if match:
                best_match, score, _ = match
                return {
                    "raw": raw_skill,
                    "normalized": best_match,
                    "confidence": round(score / 100.0, 2),
                    "method": "fuzzy"
                }
        except Exception as e:
            logger.debug(f"RapidFuzz matching failed for '{raw_skill}': {e}")
            
        # Stage 3 — Semantic similarity (Sentence Transformers)
        if self.esco_embeddings is not None:
            try:
                # Compare cosine similarity to top-100 canonical skills
                top_100 = process.extract(
                    raw_clean,
                    self.canonical_skills,
                    processor=utils.default_process,
                    limit=100
                )
                if top_100:
                    indices = [item[2] for item in top_100]
                    candidate_embs = self.esco_embeddings[indices]
                    
                    raw_emb = self.model.encode(raw_clean, convert_to_tensor=True).to(self.esco_embeddings.device)
                    cos_scores = util.cos_sim(raw_emb, candidate_embs)[0]
                    
                    best_idx = torch.argmax(cos_scores).item()
                    best_score = cos_scores[best_idx].item()
                    best_match = top_100[best_idx][0]
                    
                    if best_score >= self.semantic_threshold:
                        return {
                            "raw": raw_skill,
                            "normalized": best_match,
                            "confidence": round(best_score, 2),
                            "method": "semantic"
                        }
            except Exception as e:
                logger.error(f"Semantic matching failed for '{raw_skill}': {e}", exc_info=True)
                
        # Unknown fallback
        return {
            "raw": raw_skill,
            "normalized": raw_clean,
            "confidence": 0.0,
            "method": "unknown"
        }

    def clean_raw_skills(self, skills_section_text: str) -> List[str]:
        """
        Parses and splits skills section text into clean individual raw skill tokens.
        """
        if not skills_section_text:
            return []
            
        # Split by typical separators, ignoring delimiters inside parentheses
        parts = []
        current = []
        paren_depth = 0
        i = 0
        n = len(skills_section_text)
        
        while i < n:
            char = skills_section_text[i]
            if char in {"(", "[", "{"}:
                paren_depth += 1
                current.append(char)
                i += 1
            elif char in {")", "]", "}"}:
                paren_depth = max(0, paren_depth - 1)
                current.append(char)
                i += 1
            # Split on space-surrounded slash " / " or pipe " | " when outside parentheses
            elif paren_depth == 0 and char in {"/", "|"} and i > 0 and i + 1 < n and skills_section_text[i-1].isspace() and skills_section_text[i+1].isspace():
                parts.append("".join(current).rstrip())
                current = []
                i += 2  # Skip the slash and the trailing space
            elif char in {",", ";", "|", "\n", "•", "‣", "◦", "▪", "▫", "\t"} and paren_depth == 0:
                parts.append("".join(current))
                current = []
                i += 1
            else:
                current.append(char)
                i += 1
                
        if current:
            parts.append("".join(current))
            
        cleaned_skills = []
        seen = set()
        
        for token in parts:
            cleaned = token.strip()
            # Strip common starting bullet/list characters
            cleaned = re.sub(r'^[-\*\+\s•]+', '', cleaned)
            # Strip common trailing whitespace, hyphens, and asterisks (but keep '+' and '#')
            cleaned = re.sub(r'[-\*\s]+$', '', cleaned).strip()
            
            # Strip section headers / prefix labels (e.g. "Technical Skills: React" -> "React")
            cleaned = re.sub(r'^(?:technical\s+|soft\s+|key\s+|core\s+)?skills\s*:\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'^(?:tools|technologies|languages|competencies)\s*:\s*', '', cleaned, flags=re.IGNORECASE)
            
            if not cleaned:
                continue
                
            # Filter out tokens that are clearly not skills (too long or too short)
            if len(cleaned) > 100:  # Allow slightly longer for parenthetical content
                continue
                
            # Skip common noise terms
            if cleaned.lower() in {"and", "with", "using", "skills", "proficient in", "experience in"}:
                continue
                
            norm = cleaned.lower()
            if norm not in seen:
                seen.add(norm)
                cleaned_skills.append(cleaned)
                
        return cleaned_skills

    def normalize_skills_list(self, skills_section_text: str) -> List[Dict[str, Any]]:
        """
        Parses, splits and normalizes all skills from a section text block.
        Maintains backward compatibility with the parse router and database schema.
        """
        raw_skills = self.clean_raw_skills(skills_section_text)
        results = []
        for raw in raw_skills:
            norm = self.normalize_single_skill(raw)
            results.append({
                "skill_raw": norm["raw"],
                "skill_normalized": norm["normalized"],
                "confidence": norm["confidence"],
                "method": norm["method"]
            })
        return results

# Global lazy normalizer instance
_normalizer = None

def get_normalizer() -> SkillNormalizer:
    global _normalizer
    if _normalizer is None:
        _normalizer = SkillNormalizer()
    return _normalizer

def normalize_skills(skill_list: List[str]) -> List[Dict[str, Any]]:
    """
    Normalizes raw extracted skill strings using a 3-stage pipeline:
    Stage 1 — Exact match (ESCO ontology)
    Stage 2 — Fuzzy match (RapidFuzz, score >= 80)
    Stage 3 — Semantic similarity (Sentence Transformers, similarity >= 0.75)
    """
    if not skill_list:
        return []
        
    normalizer = get_normalizer()
    results = []
    for skill in skill_list:
        results.append(normalizer.normalize_single_skill(skill))
    return results
