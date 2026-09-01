from fastapi import APIRouter

from app.api.schemas.analyze import RagSearchRequest
from app.rag import vector_store
from app.rag.ingest import run_ingestion
from app.rag.retriever import search

router = APIRouter()


@router.post("/api/rag/ingest")
async def ingest_documents():
    """
    Discovers and ingests all PDFs under backend/data/documents/{company}/*.pdf.
    Safe to call repeatedly — unchanged files are skipped automatically.
    """
    stats = run_ingestion()
    return {"status": "ok", **stats, "total_chunks_in_store": vector_store.count()}


@router.post("/api/rag/search")
async def search_documents(payload: RagSearchRequest):
    results = search(payload.query, company=payload.company, top_k=payload.top_k)
    return {"query": payload.query, "results": results, "count": len(results)}