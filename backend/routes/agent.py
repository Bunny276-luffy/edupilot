"""
Agent / Search / Admin API routes:
  POST /api/search/papers   — Elasticsearch full-text search
  GET  /api/admin/traces    — Arize Phoenix trace log
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.elastic_service import search_papers, index_question
from services.arize_service import get_recent_traces

router = APIRouter(tags=["Agent"])


class SearchRequest(BaseModel):
    query: str
    subject: Optional[str] = None
    top_k: int = 5


class IndexRequest(BaseModel):
    question_text: str
    subject: str
    topic: str
    year: int
    source_document: str
    page: int = 1
    university: str = ""


@router.post("/api/search/papers")
async def search_past_papers(req: SearchRequest):
    """
    Search past question papers from Elasticsearch.
    Returns top_k results with highlighted matched terms.
    """
    try:
        results = await search_papers(
            query=req.query,
            subject=req.subject,
            top_k=req.top_k,
        )
        return {"query": req.query, "results": results, "count": len(results)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/search/index")
async def index_paper_question(req: IndexRequest):
    """Index a single question into Elasticsearch."""
    try:
        doc_id = await index_question(req.model_dump())
        return {"id": doc_id, "message": "Indexed successfully"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/traces")
async def get_traces(limit: int = 20):
    """
    Return last `limit` Gemini API traces from Arize Phoenix in-memory store.
    """
    try:
        traces = await get_recent_traces(limit=limit)
        return {
            "traces": traces,
            "count": len(traces),
            "note": "Traces from MongoDB and in-memory store.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
