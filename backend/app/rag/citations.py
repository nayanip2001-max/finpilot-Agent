"""
Formats retrieved evidence into the citation shape the frontend Evidence
Panel expects, and provides the guardrail message for when no relevant
document evidence exists. Never invent a citation that isn't backed by an
actual retrieved chunk.
"""
from __future__ import annotations

from typing import Any, Dict, List

INSUFFICIENT_EVIDENCE_MESSAGE = "Insufficient documentary evidence."


def format_citations(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted = []
    for e in evidence:
        formatted.append({
            "document": e.get("source"),
            "company": e.get("company"),
            "page": e.get("page"),
            "excerpt": (e.get("text") or "")[:400],
            "relevance_score": e.get("score"),
        })
    return formatted