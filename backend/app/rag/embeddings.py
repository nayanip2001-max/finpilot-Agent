"""
Local embedding model wrapper (sentence-transformers). Loaded lazily and
cached as a module-level singleton so it's only loaded once per process.

Using a local model (default: all-MiniLM-L6-v2) means embeddings never
depend on a paid API, satisfying the "no paid APIs for core demo" constraint.
"""
from __future__ import annotations

import logging
from typing import List

from app.config import get_settings

logger = logging.getLogger("finpilot.rag.embeddings")

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        logger.info("Loading embedding model '%s' (first call only)...", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()