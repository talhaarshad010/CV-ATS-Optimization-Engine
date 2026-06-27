# CV-ATS Optimization Engine

An enterprise-grade, AI-powered CV extraction, normalization, and ATS scoring platform featuring a Liquid Glass user interface. Built with FastAPI, SpaCy, Transformers (BERT/SBERT), PyTorch (Metal-accelerated ESCO normalization), and local LLMs via Ollama.

## Key Features

1. **Structured CV Parsing**: Layout-aware text extraction from PDF and DOCX files.
2. **Hybrid NER Classifier**: Extracts candidate name, email, phone, location, and computes total experience duration using SpaCy and BERT Fallback.
3. **ESCO Skill Normalization**: Maps raw resume skills to the standardized ESCO taxonomy using semantic sentence-transformer embeddings (`all-MiniLM-L6-v2`) and RapidFuzz edit-distance fallback.
4. **ATS Match Scorer & SHAP Explainer**: Computes semantic match scores against target Job Descriptions, auditing matches across 7 distinct criteria and highlighting strengths and gaps through SHAP (SHapley Additive exPlanations) values.
5. **AI Improvement Suite**: Rewrites resume bullet points to emphasize metrics and creates study roadmaps/curriculums (free courses and practice projects) to bridge missing skill gaps.
6. **Career RAG Assistant**: Interactive chatbot capable of answering questions about resume content and ATS score matches.
7. **Bulk CV Processor**: Uploads and parses multiple CVs in a batch, presenting a ranked leaderboard of candidates sorted by ATS Match Score.
8. **Interactive Analytics Dashboard**: Explores parsed candidate catalogs, match activity logs, and aggregate platform metrics.

---

## Local Setup & Quick Start

### 1. Backend Service (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env and configure Supabase Credentials
cp .env.example .env

# Run server on port 8000
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) to explore Swagger API endpoints.

### 2. Frontend Web App (Next.js)
```bash
cd frontend
npm install # or yarn install
yarn dev
```
Open [http://localhost:3000](http://localhost:3000) to access the Liquid Glass web interface.

---

## Project Directory Map

```
cv-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point & CORS configuration
│   │   ├── routers/             # API Endpoints (Upload, Parse, Score, AI, Dashboard)
│   │   ├── services/            # NLP, ESCO Normalizer, ATS Matcher, AI Helper
│   │   └── utils/               # Supabase and DB client configs
│   ├── requirements.txt         # Python dependencies list
│   └── .env.example
├── frontend/
│   ├── app/                     # Next.js Page routers & Liquid Glass style definitions
│   │   ├── globals.css          # Visual variables, animations, glass properties
│   │   ├── score/               # Scorer (Single Mode & Bulk Mode Leaderboard)
│   │   ├── improve/             # Rewriter tabs, skill gaps table, RAG chat
│   │   └── dashboard/           # Metrics panels & candidate catalog
│   ├── components/              # Frosted glass common layout blocks (Navbar)
│   └── package.json
├── ml/                          # MLflow Experiments, notebooks, and models
└── docker-compose.yml           # Multi-container orchestration (Ollama, MLflow, App)
```
