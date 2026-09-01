"""
Simple sliding-window text chunker. Each chunk retains the page number it
came from so citations can always point back to (document, page).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterator, List

from app.rag.loader import PageText


@dataclass
class Chunk:
    chunk_id: str
    company: str
    doc_name: str
    page: int
    text: str


def _split_words(text: str, chunk_size: int, overlap: int) -> Iterator[str]:
    words = text.split()
    if not words:
        return
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        piece = words[start:start + chunk_size]
        if not piece:
            break
        yield " ".join(piece)
        if start + chunk_size >= len(words):
            break


def chunk_pages(pages: List[PageText], chunk_size: int = 220, overlap: int = 40) -> List[Chunk]:
    chunks: List[Chunk] = []
    for page in pages:
        for idx, piece in enumerate(_split_words(page.text, chunk_size, overlap)):
            raw_id = f"{page.company}:{page.doc_name}:{page.page}:{idx}"
            chunk_id = hashlib.sha1(raw_id.encode()).hexdigest()[:16]
            chunks.append(Chunk(
                chunk_id=chunk_id,
                company=page.company,
                doc_name=page.doc_name,
                page=page.page,
                text=piece,
            ))
    return chunks