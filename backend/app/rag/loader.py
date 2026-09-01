"""
PDF loading: discovers PDFs under backend/data/documents/{company}/*.pdf and
extracts text page-by-page (page numbers preserved for citations) using PyMuPDF.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

import fitz  # PyMuPDF

from app.config import get_settings


@dataclass
class PageText:
    company: str          # folder name, e.g. "reliance"
    doc_name: str          # filename, e.g. "annual_report.pdf"
    page: int               # 1-indexed page number
    text: str
    file_hash: str          # sha256 of the source file, used for re-ingestion detection


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_pdfs(documents_dir: str | None = None) -> List[Path]:
    settings = get_settings()
    root = Path(documents_dir or settings.documents_path)
    if not root.exists():
        return []
    return sorted(root.glob("*/*.pdf"))


def extract_pages(pdf_path: Path) -> Iterator[PageText]:
    company = pdf_path.parent.name
    doc_name = pdf_path.name
    h = file_hash(pdf_path)
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                yield PageText(company=company, doc_name=doc_name, page=i, text=text, file_hash=h)