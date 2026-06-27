import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        # Do not print page number on cover page (Page 1)
        if self._pageNumber == 1:
            return
        
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#6e6e73'))
        
        # Header
        self.drawString(40, 755, "CV Platform System Documentation — Project Audit & Architecture Manual")
        self.setStrokeColor(colors.HexColor('#e8e8ed'))
        self.setLineWidth(0.5)
        self.line(40, 747, 572, 747)
        
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 40, page_text)
        self.drawString(40, 40, "CONFIDENTIAL — STRICTLY FOR PLATFORM INTERNAL USE ONLY")
        self.line(40, 52, 572, 52)
        
        self.restoreState()

def generate_doc():
    pdf_path = "/Users/muhammadtalhaarshad/Downloads/cv-platform/frontend/assets/CV_Platform_Documentation.pdf"
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Monochrome Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.black,
        alignment=0,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#3a3a3c'),
        alignment=0,
        spaceAfter=200
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1d1d1f'),
        alignment=0
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.black,
        spaceBefore=10,
        spaceAfter=15,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1d1d1f'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor('#2c2c2e'),
        spaceAfter=10
    )
    
    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1c1c1e'),
        backColor=colors.HexColor('#f5f5f7'),
        borderColor=colors.HexColor('#e8e8ed'),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=10
    )

    story = []

    # ═══════════════════════════════════════════════════════
    # PAGE 1: COVER
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 100))
    story.append(Paragraph("CV Platform", title_style))
    story.append(Paragraph("Comprehensive System Architecture & Component Documentation", ParagraphStyle('CoverSubTitleText', parent=title_style, fontSize=18, leading=22, textColor=colors.HexColor('#3a3a3c'), spaceAfter=8)))
    story.append(Paragraph("A Detailed Design Guide for AI-Powered CV Extraction, Skill Normalization, and ATS Matching Scorer Engine", subtitle_style))
    story.append(Spacer(1, 120))
    story.append(Paragraph("<b>Version:</b> 1.0.0 (Production Release)<br/>"
                           "<b>Author:</b> Lead AI Solutions Architect<br/>"
                           "<b>Technology Stack:</b> Next.js (V14), FastAPI, Supabase, SpaCy, Transformers, Ollama, Llama 3.1<br/>"
                           "<b>Date:</b> June 2026", meta_style))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 2: TABLE OF CONTENTS & EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("1. Executive Summary & Table of Contents", h1_style))
    story.append(Paragraph(
        "The CV Platform is an enterprise-grade application designed to automate the lifecycle of talent profiling. "
        "It ingests unstructured resumes (PDF/DOCX), processes them through advanced layout-aware parsers, cleans "
        "the text, segments content into structured sections, runs Named Entity Recognition (NER), normalizes "
        "skills against the ESCO taxonomy, and computes an ATS Match Score against job descriptions using SHAP value explanations.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Document Outline & Table of Contents:</b><br/>"
        "• Page 1: Cover Page<br/>"
        "• Page 2: Table of Contents & Executive Summary<br/>"
        "• Page 3: Core System Architecture & Directory Layout<br/>"
        "• Page 4: Frontend App Directory & Layouts<br/>"
        "• Page 5: Frontend Page Routers & Dynamic Components<br/>"
        "• Page 6: Backend Base Setup & Utility Modules<br/>"
        "• Page 7: Backend API Routers & Endpoints<br/>"
        "• Page 8: Extraction & Natural Language Processing (NLP) Engine<br/>"
        "• Page 9: Named Entity Recognition (NER) & Profile Parsing<br/>"
        "• Page 10: Skill Normalization Engine & ESCO Taxonomy<br/>"
        "• Page 11: ATS Match Scoring & SHAP Explainer<br/>"
        "• Page 12: AI Improvement Engine & Local RAG Assistant<br/>"
        "• Page 13: Database & Cloud Storage Architecture<br/>"
        "• Page 14: Automated MLflow Tracking System<br/>"
        "• Page 15: Containerization & DevOps Setup",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 3: CORE SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("2. Core System Architecture & Directory Layout", h1_style))
    story.append(Paragraph(
        "The CV Platform is designed as a decoupled, microservices-oriented architecture consisting of three primary layers:<br/>"
        "1. <b>Frontend Layer</b>: A Next.js Web Application written in TypeScript, using TailwindCSS and custom Liquid Glass components.<br/>"
        "2. <b>Backend Layer</b>: A high-performance FastAPI service running Python 3.11/3.13, orchestrating NLP pipelines and AI models.<br/>"
        "3. <b>Database and Storage Layer</b>: Powered by Supabase, providing PostgreSQL, RLS policies, and raw file storage buckets.",
        body_style
    ))
    story.append(Paragraph("Directory Structure Overview:", h2_style))
    story.append(Paragraph(
        "cv-platform/<br/>"
        "├── backend/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# FastAPI Python Backend<br/>"
        "│ &nbsp;&nbsp;├── app/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# API Source Code<br/>"
        "│ &nbsp;&nbsp;│ &nbsp;&nbsp;├── routers/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Endpoints definitions<br/>"
        "│ &nbsp;&nbsp;│ &nbsp;&nbsp;├── services/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# NLP, ESCO, ATS models<br/>"
        "│ &nbsp;&nbsp;│ &nbsp;&nbsp;└── utils/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Database, helpers<br/>"
        "│ &nbsp;&nbsp;└── generate_perfect_cv.py &nbsp;# CV generation utility<br/>"
        "├── frontend/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Next.js Frontend Application<br/>"
        "│ &nbsp;&nbsp;├── app/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Next.js routers & styles<br/>"
        "│ &nbsp;&nbsp;├── components/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Translucent glass UI components<br/>"
        "│ &nbsp;&nbsp;└── lib/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Store & API Axios clients<br/>"
        "└── docker-compose.yml &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Multi-container local deployment",
        code_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 4: FRONTEND APP DIRECTORY & LAYOUTS
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("3. Frontend App Directory & Layouts", h1_style))
    story.append(Paragraph(
        "The frontend is structured around Next.js App Router. The styling system is configured using Vanilla TailwindCSS "
        "interleaved with custom glassmorphism styles defined in `globals.css`.",
        body_style
    ))
    story.append(Paragraph("Key Global Files:", h2_style))
    story.append(Paragraph(
        "<b>1. frontend/app/globals.css</b>:<br/>"
        "Defines the visual custom properties for the Liquid Glass system. Variables like <code>--glass-bg</code>, "
        "<code>--glass-border</code>, and <code>--glass-shadow</code> are set to translucent whites with subtle contrast borders "
        "under a general off-white body background. It also includes keyframe animations like <code>fadeInUp</code>, "
        "<code>shimmer</code>, and <code>borderPulse</code> to provide micro-animations for card entries and loadings.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. frontend/app/layout.tsx</b>:<br/>"
        "Sets the default HTML skeleton, imports Google Font <i>Inter</i> via Next.js Font Optimizations, "
        "and sets the layout background to the off-white CSS gradient. It wraps the entire document inside the "
        "<code>AppProvider</code> to store state variables across pages, and displays the global sticky <code>Navbar</code>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. frontend/components/Navbar.tsx</b>:<br/>"
        "A sticky, frosted glass navigation header. It dynamically highlights the current path and fetches parameters "
        "from the global store. For example, if a candidate has been analyzed, it appends <code>candidate_id</code> query "
        "parameters automatically to navigations like 'Score Match' and 'Improve CV' so users do not lose their current profile.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 5: FRONTEND PAGE ROUTERS
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("4. Frontend Page Routers & Dynamic Components", h1_style))
    story.append(Paragraph(
        "The client application is organized into 4 main page routers, each corresponding to a major user goal:",
        body_style
    ))
    story.append(Paragraph("App Pages & Files:", h2_style))
    story.append(Paragraph(
        "<b>1. frontend/app/page.tsx (Upload Page)</b>:<br/>"
        "Responsible for handling drag-and-drop file inputs (PDF/DOCX) using <code>react-dropzone</code>. Once a file is drop-selected, "
        "it triggers the <code>/upload</code> API endpoint, updating upload progress dynamically. After raw text extraction completes, "
        "it renders an editable CV Parser Preview card allowing the candidate to fix fields in real-time. Changes are saved back to "
        "the database via a <code>Save Details</code> button before redirecting to scoring.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. frontend/app/score/page.tsx (Match Scorer)</b>:<br/>"
        "Computes the compliance between a CV and a job description. It renders a circular progress gauge representing the final "
        "ATS score, prints top positive and negative SHAP attribution cards, and formats matched/missing skills side-by-side. It also "
        "contains a timeline representation of suggested study paths.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. frontend/app/improve/page.tsx (AI Optimizer)</b>:<br/>"
        "An AI-powered 3-tab workbench to improve the resume. Includes: 1. <i>Bullet Points Optimizer</i> (rewriting experience points "
        "using metrics), 2. <i>Skill Gaps</i> (table of course/project curriculum suggestions), and 3. <i>Chat Assistant</i> (a RAG chat form).",
        body_style
    ))
    story.append(Paragraph(
        "<b>4. frontend/app/dashboard/page.tsx (Analytics)</b>:<br/>"
        "Collects and charts platform-wide aggregate metrics (total candidates, total matches, average scores) and displays "
        "a catalog list of previously processed candidate records.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 6: BACKEND BASE SETUP
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("5. Backend Base Setup & Utility Modules", h1_style))
    story.append(Paragraph(
        "The backend is powered by FastAPI. Uvicorn acts as the ASGI web server, supporting live-reloading during local "
        "development. The system coordinates configurations using environment variables mounted from `.env` files.",
        body_style
    ))
    story.append(Paragraph("Core Backend Modules:", h2_style))
    story.append(Paragraph(
        "<b>1. backend/app/main.py</b>:<br/>"
        "The application bootstrapper. It initializes the <code>FastAPI</code> instance and mounts the CORS middleware, "
        "explicitly authorizing cross-origin resource sharing from the local frontend origin (<code>http://localhost:3000</code>). "
        "It also aggregates and mounts routers for all modules under the unified <code>/api/v1</code> prefix.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. backend/app/utils/supabase_client.py</b>:<br/>"
        "Serves as the database and storage driver. It wraps the official Supabase Python client using environment keys "
        "(<code>SUPABASE_URL</code> and <code>SUPABASE_SERVICE_ROLE_KEY</code>). "
        "It exposes wrapper functions for: <br/>"
        "• <code>upload_file_to_storage</code>: Uploads raw PDF/DOCX bytes to the <code>resumes</code> bucket.<br/>"
        "• <code>insert_candidate</code> / <code>update_candidate</code>: Updates parsing details and state fields in the database.<br/>"
        "• <code>bulk_insert_extracted_skills</code>: Stores NLP-mapped skills into the <code>extracted_skills</code> relation table.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 7: BACKEND API ROUTERS
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("6. Backend API Routers & Endpoints", h1_style))
    story.append(Paragraph(
        "The backend divides routing logic into distinct sub-modules inside the <code>app/routers/</code> directory, "
        "mapping RESTful routes to specific database and NLP services:",
        body_style
    ))
    story.append(Paragraph("Active API Endpoints:", h2_style))
    story.append(Paragraph(
        "<b>1. upload.py -> POST /api/v1/upload</b>:<br/>"
        "Handles multipart form file uploads. Validates file types (PDF/DOCX) and file sizes (< 10MB). "
        "Triggers the extraction engine, writes the raw document bytes to Supabase Storage, registers the candidate "
        "in the database with status <code>extracted</code>, and returns the parsed character count and raw text payload.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. parse.py -> POST /api/v1/parse/{candidate_id} & PUT /api/v1/candidates/{candidate_id}</b>:<br/>"
        "The POST route runs text cleaning, section detection, hybrid Named Entity Recognition, and ESCO skill normalization. "
        "It updates the candidate row status to <code>parsed</code>. The PUT route enables frontend manual edits to be stored.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. jobs.py -> POST /api/v1/jobs</b>:<br/>"
        "Registers a target job description and extracts its key tech keywords and role parameters.",
        body_style
    ))
    story.append(Paragraph(
        "<b>4. score.py -> POST /api/v1/score</b>:<br/>"
        "Orchestrates the ATS scoring matching logic and computes SHAP value attributions.",
        body_style
    ))
    story.append(Paragraph(
        "<b>5. ai.py & dashboard.py -> GET /api/v1/dashboard</b>:<br/>"
        "ai.py mounts rewriter, gaps, and chat prompts. dashboard.py provides metric counts and logs.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 8: EXTRACTION & TEXT NLP ENGINE
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("7. Extraction & Text NLP Engine", h1_style))
    story.append(Paragraph(
        "Before applying deep learning models, raw documents must be converted into clean, contiguous text. "
        "This is handled by dedicated text processing services in the <code>app/services/</code> directory:",
        body_style
    ))
    story.append(Paragraph("Files & Algorithms:", h2_style))
    story.append(Paragraph(
        "<b>1. app/services/extractor.py (Document Reader)</b>:<br/>"
        "Utilizes <code>PyMuPDF</code> (imported as <code>fitz</code>) to read PDFs. It extracts text with layout-aware "
        "parameters (<code>sort=True</code>) ensuring multi-column text blocks are grouped vertically instead of "
        "collapsing horizontally. For Word documents, it parses paragraphs and tables using the <code>python-docx</code> library.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. app/services/cleaner.py (Text Normalizer)</b>:<br/>"
        "Cleans the raw text. It decodes smart quotes (e.g. converting curly quotes to straight quotes), maps em dashes, "
        "strips non-printable control symbols, normalizes unicode spacing, and collapses redundant line breaks. "
        "This prevents formatting anomalies from disrupting NLP classifiers.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. app/services/section_detector.py (Section Segmentation)</b>:<br/>"
        "Scans the cleaned text line-by-line to detect section boundaries. It uses case-insensitive regular expressions "
        "matching common headings (e.g. Summary, Education, Experience, Skills, Projects, Certifications, Languages, Achievements). "
        "Once boundaries are established, it returns segmented text chunks. Chunks with less than 20 characters are flagged as "
        "<code>low confidence</code>, while larger blocks are labeled <code>high confidence</code>.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 9: NAMED ENTITY RECOGNITION (NER)
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("8. Named Entity Recognition (NER) & Profile Parsing", h1_style))
    story.append(Paragraph(
        "Extracting contact info (name, email, phone, location) and professional duration from unstructured text is "
        "achieved via a hybrid Named Entity Recognition pipeline inside <code>ner_orchestrator.py</code>.",
        body_style
    ))
    story.append(Paragraph("Hybrid Pipeline Steps:", h2_style))
    story.append(Paragraph(
        "<b>Step 1: SpaCy NER Classifier</b>:<br/>"
        "The system loads the spaCy model <code>en_core_web_sm</code> to extract standard entities like <code>PERSON</code>, "
        "<code>EMAIL</code>, <code>GPE</code> (locations), and <code>ORG</code> (companies/universities) from the personal info section.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Step 2: BERT fallback</b>:<br/>"
        "If spaCy fails to isolate a name or email, it calls the HuggingFace transformer pipeline <code>dslim/bert-base-NER</code>. "
        "The system merges entities, resolving duplicate token spans.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Step 3: Location GPE Blacklisting</b>:<br/>"
        "Common technical keywords (like <code>AI</code>, <code>UI</code>, <code>Next.js</code>) are frequently misclassified by "
        "standard models as location entities (GPE). The GPE parser filters extracted strings against a strict blacklist "
        "to ensure locations like 'Karachi, Pakistan' are correctly preserved.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Step 4: Experience Duration Summing</b>:<br/>"
        "The system scans the experience text for date ranges (e.g., 'Aug 2022 - May 2024') using regex. It parses month and "
        "year boundaries using <code>python-dateutil</code>, sums the durations, and returns the total experience in years.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 10: SKILL NORMALIZATION ENGINE
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("9. Skill Normalization Engine & ESCO Taxonomy", h1_style))
    story.append(Paragraph(
        "To make resume skills searchable and comparable, they must be normalized against a standardized taxonomy. "
        "The CV Platform utilizes the European Skills, Competences, Qualifications and Occupations (ESCO) taxonomy.",
        body_style
    ))
    story.append(Paragraph("Normalization Mechanics:", h2_style))
    story.append(Paragraph(
        "<b>1. Token splitting</b>:<br/>"
        "The skills section text is tokenized using parenthesis-aware delimiters. It splits on commas, semicolons, "
        "slashes, and pipes (e.g. <code>,</code>, <code>/</code>, <code>|</code>) only when they reside outside "
        "of parenthesis. This ensures that compound skill descriptions like 'React Native (Core / Bridge)' are "
        "preserved as a single item instead of being split incorrectly.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. Embedding search</b>:<br/>"
        "The normalizer loads the SentenceTransformer model <code>all-MiniLM-L6-v2</code>. It generates vector embeddings "
        "for the extracted skill string and performs cosine similarity search against a pre-compiled dataset of "
        "ESCO preferred skill terms. On Apple Silicon, it accelerates calculations using the PyTorch <code>mps</code> (Metal) GPU backend.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. Tech Overrides & RapidFuzz Fallback</b>:<br/>"
        "For common software terms (e.g. <code>FastAPI</code>, <code>Vite</code>) that might not map cleanly in ESCO, "
        "a hardcoded dictionary overrides standard searches. If similarity scores fall below 0.7, the engine runs "
        "a string edit distance search using the <code>RapidFuzz</code> library as a fallback to resolve typos.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 11: ATS MATCH SCORING & SHAP EXPLAINER
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("10. ATS Match Scoring & SHAP Explainer", h1_style))
    story.append(Paragraph(
        "The ATS Match Scorer (<code>app/services/ats_scorer.py</code>) calculates the overall match score between a candidate "
        "profile and a job description. The score is computed as a weighted average across multiple criteria:",
        body_style
    ))
    story.append(Paragraph("Weighted Scoring Rubric:", h2_style))
    story.append(Paragraph(
        "• <b>Skills Alignment (40%)</b>: Computes the ratio of matched normalized skills to target job requirements.<br/>"
        "• <b>Experience Match (20%)</b>: Audits total candidate experience years against target job requirements.<br/>"
        "• <b>Semantic Similarity (15%)</b>: Runs sentence embedding similarity between the resume text and the job description.<br/>"
        "• <b>Education Audit (10%)</b>: Scans the education block for matching degree titles (e.g., Bachelor, Master, PhD).<br/>"
        "• <b>Project Relevance (5%)</b>: Compares project details to job criteria using word embeddings.<br/>"
        "• <b>Certifications (5%)</b>: Checks for presence of industry certifications.<br/>"
        "• <b>Resume Quality (5%)</b>: Audits text parameters like spelling and section structure.",
        body_style
    ))
    story.append(Paragraph("SHAP Feature Contributions:", h2_style))
    story.append(Paragraph(
        "Rather than outputting a black-box percentage, the scorer calculates <b>SHAP (SHapley Additive exPlanations)</b> "
        "values for each category. It models the scoring equation as a game where each sub-criteria is a player. "
        "It outputs top positive contributions (e.g., '+15% due to Python skill match') and top negative contributions "
        "(e.g., '-10% due to missing cloud deployment experience') to help candidates audit their score.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 12: AI IMPROVEMENT ENGINE
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("11. AI Improvement Engine & Local RAG Assistant", h1_style))
    story.append(Paragraph(
        "Once gaps are identified, the CV Platform provides automated suggestions via local AI endpoints, "
        "prompting an Ollama server running Llama 3.1 8B Instruct model:",
        body_style
    ))
    story.append(Paragraph("Key Improvement Features:", h2_style))
    story.append(Paragraph(
        "<b>1. Bullet Points Optimizer</b>:<br/>"
        "Accepts a target role and original resume bullets. The Llama 3.1 model refactors each bullet point, "
        "replacing weak verbs with strong action verbs (e.g. 'wrote Python code' -> 'Engineered Python API layers') "
        "and inserts metric placeholders (e.g. '[X]%') to encourage quantitative impact descriptions.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. Skill Gap curriculum builder</b>:<br/>"
        "For each missing skill identified in the scoring phase, the system prompts Llama 3.1 to return a study roadmap. "
        "The model suggests: 1. A free online learning course name, 2. A hands-on practice project to build, and 3. An "
        "estimated study period in weeks, representing priority levels (High/Medium/Low) for acquisition.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. RAG Chat Assistant</b>:<br/>"
        "Supports direct career Q&A. The candidate's resume and current ATS score audit details are loaded into a vector "
        "context store. When the user asks a question (e.g. 'Why is my ATS score low?'), the system retrieves "
        "matching context blocks, injecting them into the system prompt of Llama 3.1 for a context-aware answer.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 13: DATABASE & CLOUD STORAGE
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("12. Database & Cloud Storage Architecture", h1_style))
    story.append(Paragraph(
        "The database layer is managed by PostgreSQL hosted on Supabase. Relational models enforce integrity "
        "across candidates, skills, and evaluation scores.",
        body_style
    ))
    story.append(Paragraph("Core Database Tables:", h2_style))
    story.append(Paragraph(
        "<b>1. candidates table</b>:<br/>"
        "Stores the primary profile records. Columns include: <code>id</code> (UUID primary key), <code>file_name</code>, "
        "<code>file_path</code> (Supabase Storage reference path), <code>candidate_name</code>, <code>email</code>, "
        "<code>phone</code>, <code>location</code>, <code>linkedin_url</code>, <code>total_experience_years</code>, "
        "<code>raw_text</code>, <code>raw_sections</code> (JSONB storing split sections), <code>raw_entities</code> (JSONB storing entities), "
        "<code>status</code> (extracted/parsed), and <code>created_at</code>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. extracted_skills table</b>:<br/>"
        "Stores the NLP-normalized skills. Columns include: <code>id</code>, <code>candidate_id</code> (Foreign Key referencing candidates), "
        "<code>skill_raw</code>, <code>skill_normalized</code> (matched ESCO label), <code>confidence</code>, and <code>created_at</code>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. ats_scores table</b>:<br/>"
        "Logs matching history. Columns include: <code>id</code>, <code>candidate_id</code>, <code>job_title</code>, "
        "<code>ats_score</code> (numeric percentage), <code>grade</code>, <code>breakdown</code> (JSONB storing category scores), "
        "<code>recommendation</code>, <code>created_at</code>.",
        body_style
    ))
    story.append(Paragraph("Cloud Storage Buckets:", h2_style))
    story.append(Paragraph(
        "The platform includes a storage bucket named <code>resumes</code>. Row-Level Security (RLS) public policies "
        "allow write (<code>INSERT</code>) and read (<code>SELECT</code>) access to raw resume PDF files.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 14: AUTOMATED MLFLOW TRACKING SYSTEM
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("13. Automated MLflow Tracking System", h1_style))
    story.append(Paragraph(
        "To monitor parsing quality and model drift, the platform integrates <b>MLflow Tracking</b>. "
        "Whenever a CV is analyzed, a tracking run is initiated.",
        body_style
    ))
    story.append(Paragraph("MLflow Logs Architecture:", h2_style))
    story.append(Paragraph(
        "<b>1. Run Context</b>:<br/>"
        "Runs are registered under a default experiment name. MLflow stores tracking data locally in "
        "<code>./ml/mlruns</code>, ensuring offline functionality.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. Logged Parameters</b>:<br/>"
        "• <code>candidate_id</code>: Unique reference key.<br/>"
        "• <code>ner_method</code>: Method utilized (e.g. <code>spacy</code> or <code>bert</code> fallback).<br/>"
        "• <code>skill_count</code>: Total skills extracted.<br/>"
        "• <code>char_count</code>: Size of raw extracted text.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. Logged Metrics</b>:<br/>"
        "• <code>parsing_duration_seconds</code>: Time taken by the pipeline to segment and tag.<br/>"
        "• <code>total_experience_years</code>: Numeric experience years.",
        body_style
    ))
    story.append(Paragraph(
        "<b>4. Logged Artifacts</b>:<br/>"
        "• <code>raw_text.txt</code>: The complete cleaned raw text parsed from PyMuPDF.<br/>"
        "• <code>parsed_profile.json</code>: The structured candidate payload returned by the NER engine.",
        body_style
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 15: CONTAINERIZATION & DEVOPS SETUP
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("14. Containerization & DevOps Setup", h1_style))
    story.append(Paragraph(
        "The entire platform is containerized using Docker to ensure consistent local development "
        "and production environments.",
        body_style
    ))
    story.append(Paragraph("Service Specifications:", h2_style))
    story.append(Paragraph(
        "<b>1. backend (FastAPI)</b>:<br/>"
        "Uses <code>python:3.11-slim</code>. Installs compiler tools, <code>cmake</code> (required for FAISS compiling), "
        "and graphics tools (needed for PyMuPDF layout and OCR fallbacks). Exposes port <code>8000</code>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. frontend (Next.js)</b>:<br/>"
        "Multi-stage build using <code>node:18-alpine</code>. Compiles static production pages, exposing port <code>3000</code>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. ollama (LLM Server)</b>:<br/>"
        "Runs the official <code>ollama/ollama:latest</code> image. Mounts a volume named <code>ollama_models</code> "
        "to cache downloaded LLM weights, exposing port <code>11434</code>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>4. ollama-pull (Companion Helper)</b>:<br/>"
        "A slim service that automatically triggers a curl request to Ollama once the container boots, "
        "initiating the download of the <code>llama3.1:8b-instruct-q4_K_M</code> weights.",
        body_style
    ))
    story.append(Paragraph(
        "<b>5. mlflow (Tracking Server)</b>:<br/>"
        "Mounts <code>./ml/mlruns</code> to store metadata. Exposes port <code>5000</code> inside the network, "
        "mapped to host port <code>5050</code> to avoid AirPlay conflicts on macOS.",
        body_style
    ))
    
    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated 15-page project documentation at: {pdf_path}")

if __name__ == "__main__":
    generate_doc()
