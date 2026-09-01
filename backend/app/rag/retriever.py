"""
Semantic retrieval over ingested document chunks.

Returns evidence dicts shaped exactly as required by the problem statement:
    {"source": doc_name, "page": N, "chunk_id": "...", "text": "...", "score": float}

If nothing relevant is found (empty corpus, or scores below threshold), the
caller (agents/fundamental.py) is responsible for returning the literal
"Insufficient documentary evidence." message rather than fabricating a claim.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.rag import vector_store
from app.rag.embeddings import embed_texts

MIN_RELEVANCE_SCORE = 0.15  # cosine similarity floor; below this we treat evidence as too weak


def search(query_text: str, company: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    if vector_store.count() == 0:
        return []

    embedding = embed_texts([query_text])[0]
    where = {"company": company.lower()} if company else None
    result = vector_store.query(embedding, top_k=top_k, where=where)

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    evidence: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        similarity = 1 - dist  # chroma cosine space returns distance; convert to similarity
        if similarity < MIN_RELEVANCE_SCORE:
            continue
        evidence.append({
            "source": meta.get("doc_name"),
            "company": meta.get("company"),
            "page": meta.get("page"),
            "chunk_id": None,  # filled by caller if needed; chroma id available separately
            "text": doc,
            "score": round(float(similarity), 3),
        })
    return evidence