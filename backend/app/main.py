from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, parse, jobs, score, ai, dashboard

app = FastAPI(
    title="CV Platform API",
    description="AI-powered CV extraction and ATS scoring",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:3005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(parse.router, prefix="/api/v1", tags=["parse"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(score.router, prefix="/api/v1/score", tags=["score"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])




@app.get("/")
def root():
    return {"status": "ok", "message": "CV Platform API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
