import os
import csv
import logging

logger = logging.getLogger(__name__)

# Locate the ESCO CSV relative to this file
DEFAULT_CSV_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "ml",
        "data",
        "esco_skills.csv"
    )
)

# Hardcoded fallback list of common tech skills
FALLBACK_TECH_SKILLS = {
    # Programming Languages
    "python": "Python",
    "python programming": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "java script": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "c sharp": "C#",
    "c": "C",
    "ruby": "Ruby",
    "ruby on rails": "Ruby on Rails",
    "rails": "Ruby on Rails",
    "php": "PHP",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "perl": "Perl",
    "r": "R",
    "sql": "SQL",
    "pl/sql": "PL/SQL",
    "bash": "Bash",
    "shell": "Shell Scripting",
    "shell scripting": "Shell Scripting",

    # Web Frameworks & Libraries
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react native": "React Native",
    "angular": "Angular",
    "angularjs": "Angular",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "jquery": "jQuery",
    "bootstrap": "Bootstrap",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",

    # Databases
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "oracle": "Oracle Database",
    "mssql": "Microsoft SQL Server",
    "sql server": "Microsoft SQL Server",

    # DevOps & Cloud
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jenkins": "Jenkins",
    "ansible": "Ansible",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",

    # Other / Data Science / Design
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "graphql": "GraphQL",
    "rest api": "REST API",
    "rest": "REST API",
    "figma": "Figma",
    "photoshop": "Adobe Photoshop",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
}

# In-memory cached lookup structures
_lookup_dict = {}
_all_canonical_skills = []

def load_ontology(csv_path: str = DEFAULT_CSV_PATH):
    """Loads the ESCO taxonomy CSV or fallback into the cache."""
    global _lookup_dict, _all_canonical_skills
    
    _lookup_dict = {}
    canonical_set = set()
    
    if os.path.exists(csv_path):
        logger.info(f"Loading ESCO ontology from {csv_path}...")
        try:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pref = row.get("preferredLabel", "").strip()
                    if not pref:
                        continue
                    
                    # Store canonical name
                    canonical_set.add(pref)
                    
                    # Map preferred label to itself (lowercase)
                    pref_lower = pref.lower()
                    _lookup_dict[pref_lower] = pref
                    
                    # Map altLabels
                    alt_labels_str = row.get("altLabels", "")
                    if alt_labels_str:
                        # Split by newline (default ESCO CSV separator for altLabels)
                        alt_labels = [alt.strip() for alt in alt_labels_str.split("\n") if alt.strip()]
                        for alt in alt_labels:
                            _lookup_dict[alt.lower()] = pref
                            
            _all_canonical_skills = sorted(list(canonical_set))
            logger.info(f"Successfully loaded ESCO ontology: {len(_all_canonical_skills)} unique skills, {len(_lookup_dict)} total mappings.")
        except Exception as e:
            logger.error(f"Error reading ESCO CSV at {csv_path}: {e}. Falling back to hardcoded tech skills.")
    else:
        logger.warning(f"ESCO CSV not found at {csv_path}. Loading hardcoded fallback tech skills.")
        
    # Always merge fallback tech skills as high-quality overrides/additions
    for raw, canonical in FALLBACK_TECH_SKILLS.items():
        _lookup_dict[raw.lower()] = canonical
        canonical_set.add(canonical)
        
    _all_canonical_skills = sorted(list(canonical_set))
    logger.info(f"Initialized ontology with overrides: {len(_all_canonical_skills)} unique skills, {len(_lookup_dict)} total mappings.")

# Run loading on module startup
load_ontology()

def normalize_skill(raw_skill: str) -> str:
    """
    Normalizes a skill name.
    Checks for an exact match in the ontology (case-insensitive).
    Returns the canonical name if found, otherwise returns the original raw skill.
    """
    if not raw_skill:
        return ""
    
    clean_skill = raw_skill.strip()
    key = clean_skill.lower()
    
    if key in _lookup_dict:
        return _lookup_dict[key]
        
    return clean_skill

def get_all_canonical_skills() -> list[str]:
    """Returns a list of all unique canonical skill names."""
    return _all_canonical_skills
