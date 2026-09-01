"""
Thin wrapper around a persistent ChromaDB collection. Kept isolated so the
vector DB could be swapped for FAISS or a hosted store later without
touching retriever.py or the ingestion script's control flow.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger("finpilot.rag.vector_store")

_client = None
_collection = None
COLLECTION_NAME = "finpilot_documents"


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb
        settings = get_settings()
        _client = chromadb.PersistentClient(path=settings.vector_db_path)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert(ids: List[str], embeddings: List[List[float]], documents: List[str],
           metadatas: List[Dict[str, Any]]) -> None:
    if not ids:
        return
    collection = _get_collection()
    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(embedding: List[float], top_k: int = 5,
          where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    collection = _get_collection()
    return collection.query(query_embeddings=[embedding], n_results=top_k, where=where)


def count() -> int:
    try:
        return _get_collection().count()
    except Exception:  # noqa: BLE001
        return 0


def existing_file_hashes() -> Dict[str, str]:
    """Return {doc_name: file_hash} for already-ingested chunks, used to skip unchanged files."""
    try:
        collection = _get_collection()
        got = collection.get(include=["metadatas"])
        hashes: Dict[str, str] = {}
        for meta in got.get("metadatas", []):
            if meta and "doc_name" in meta and "file_hash" in meta:
                hashes[f"{meta.get('company')}/{meta['doc_name']}"] = meta["file_hash"]
        return hashes
    except Exception:  # noqa: BLE001
        return {}