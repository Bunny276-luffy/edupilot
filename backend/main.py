"""
EduPilot FastAPI Backend — main entry point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.faculty import router as faculty_router
from routes.student import router as student_router
from routes.agent import router as agent_router

app = FastAPI(
    title="EduPilot API",
    description="AI-powered academic agent for Indian colleges — NAAC/NBA automation + Socratic tutoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(faculty_router)
app.include_router(student_router)
app.include_router(agent_router)


@app.on_event("startup")
async def startup_event():
    # 1. Initialize MongoDB and check connection
    from services.mongodb_service import check_mongodb_connection
    await check_mongodb_connection()

    # 2. Initialize Elasticsearch and check connection
    from services.elastic_service import check_elastic_connection, ensure_index
    await check_elastic_connection()
    await ensure_index()

    # 3. Initialize Phoenix tracer
    from services.arize_service import init_phoenix
    init_phoenix()


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "EduPilot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check for Cloud Run."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
