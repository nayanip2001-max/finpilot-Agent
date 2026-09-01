"""
RAG ingestion pipeline.

Usage:
    python -m app.rag.ingest

Discovers PDFs under backend/data/documents/{company}/*.pdf, extracts text
(preserving page numbers), chunks it, embeds chunks locally, and upserts
into the persistent vector store. Files whose content hash hasn't changed
since the last ingestion are skipped.
"""
from __future__ import annotations

import logging
import sys
from collections import defaultdict

from app.rag import vector_store
from app.rag.chunker import chunk_pages
from app.rag.embeddings import embed_texts
from app.rag.loader import discover_pdfs, extract_pages, file_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("finpilot.rag.ingest")


def run_ingestion() -> dict:
    pdfs = discover_pdfs()
    if not pdfs:
        logger.warning(
            "No PDFs found under backend/data/documents/{company}/*.pdf. "
            "Add files there (see README) and re-run this command."
        )
        return {"files_found": 0, "files_ingested": 0, "files_skipped": 0, "chunks_upserted": 0}

    existing_hashes = vector_store.existing_file_hashes()

    stats = {"files_found": len(pdfs), "files_ingested": 0, "files_skipped": 0, "chunks_upserted": 0}

    for pdf_path in pdfs:
        company = pdf_path.parent.name
        doc_name = pdf_path.name
        key = f"{company}/{doc_name}"
        current_hash = file_hash(pdf_path)

        if existing_hashes.get(key) == current_hash:
            logger.info("SKIP (unchanged): %s", key)
            stats["files_skipped"] += 1
            continue

        logger.info("INGESTING: %s", key)
        pages = list(extract_pages(pdf_path))
        if not pages:
            logger.warning("No extractable text in %s — skipping (scanned/empty PDF?).", key)
            continue

        chunks = chunk_pages(pages)
        if not chunks:
            continue

        texts = [c.text for c in chunks]
        embeddings = embed_texts(texts)
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "company": c.company,
                "doc_name": c.doc_name,
                "page": c.page,
                "file_hash": current_hash,
            }
            for c in chunks
        ]

        vector_store.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

        stats["files_ingested"] += 1
        stats["chunks_upserted"] += len(chunks)
        logger.info("  -> %d chunks upserted from %d pages", len(chunks), len(pages))

    logger.info("Ingestion complete: %s", stats)
    return stats


if __name__ == "__main__":
    result = run_ingestion()
    sys.exit(0 if result["files_found"] >= 0 else 1)