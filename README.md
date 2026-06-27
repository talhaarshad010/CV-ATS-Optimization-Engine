# CV Platform

AI-powered CV extraction and ATS scoring platform.
Built with FastAPI, SpaCy, BERT, SBERT, PyTorch, and local LLMs via Ollama.

## Quick start (Mac)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in your Supabase credentials in .env

uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs to test the upload endpoint.

## Project structure

```
cv-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routers/
│   │   │   └── upload.py        # POST /api/v1/upload
│   │   ├── services/
│   │   │   └── extractor.py     # PDF/DOCX extraction fallback chain
│   │   ├── models/
│   │   │   └── candidate.py     # Pydantic models
│   │   └── utils/
│   │       └── supabase_client.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # Next.js (Phase 6)
├── ml/                          # Models and notebooks (Phase 2+)
├── scripts/
│   └── supabase_schema.sql      # Run in Supabase SQL Editor
└── docker-compose.yml           # Phase 6
```

## Phase progress

- [x] Phase 1 — File ingestion and extraction
- [ ] Phase 2 — Section detection and NER
- [ ] Phase 3 — Skill normalization and layout handling
- [ ] Phase 4 — ATS scoring and semantic matching
- [ ] Phase 5 — Local GenAI (Ollama + LangChain)
- [ ] Phase 6 — MLOps, dashboard, deployment
