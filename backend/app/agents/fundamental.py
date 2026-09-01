"""
Fundamental / RAG Agent — the primary RAG agent.

Pipeline: query -> semantic retrieval over ingested PDFs -> LLM reasoning
grounded ONLY in retrieved chunks -> answer + citations.

If no relevant document evidence is retrieved, this agent explicitly returns
"Insufficient documentary evidence." rather than letting the LLM fabricate
a fundamentals view. It never hallucinates citations.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.rag.citations import INSUFFICIENT_EVIDENCE_MESSAGE, format_citations
from app.rag.retriever import search
from app.utils.llm import call_llm

# Very small keyword rule to turn retrieved text into a directional lean.
# This is intentionally simple for the MVP — it looks at the same
# POSITIVE/NEGATIVE lexicon idea as sentiment, applied to filing language.
POSITIVE_TERMS = {"growth", "record", "profit", "expansion", "increase", "strong", "beat", "upgrade"}
NEGATIVE_TERMS = {"decline", "loss", "delay", "investigation", "penalty", "weak", "miss", "downgrade"}


def _lean_from_text(chunks_text: str) -> int:
    words = {w.strip(".,!?()").lower() for w in chunks_text.split()}
    return len(words & POSITIVE_TERMS) - len(words & NEGATIVE_TERMS)


class FundamentalAgent(BaseAgent):
    name = "fundamental"
    purpose = (
        "Retrieves relevant chunks from ingested regulatory/financial documents "
        "(annual reports, quarterly results, investor presentations, transcripts) "
        "via RAG and grounds a fundamentals view in that retrieved evidence, "
        "with visible source/page attribution."
    )

    async def execute(self, symbol: str, question: str | None = None, **kwargs) -> AgentResult:
        company = symbol.lower()
        query_text = question or f"{symbol} financial performance, revenue growth, and outlook"

        try:
            raw_evidence = search(query_text, company=company, top_k=5)
        except Exception as exc:  # noqa: BLE001 — degraded path, RAG failure must not crash analysis
            return AgentResult(
                agent=self.name,
                status=AgentStatus.DEGRADED,
                signal="UNKNOWN",
                confidence=0.0,
                reasons=[f"RAG retrieval failed: {exc}. {INSUFFICIENT_EVIDENCE_MESSAGE}"],
                evidence=[],
            )

        if not raw_evidence:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.DEGRADED,
                signal="NEUTRAL",
                confidence=0.15,
                reasons=[INSUFFICIENT_EVIDENCE_MESSAGE + " No ingested documents matched this query. "
                         "Run `python -m app.rag.ingest` after adding PDFs to backend/data/documents/."],
                evidence=[],
            )

        citations = format_citations(raw_evidence)
        combined_text = " ".join(e["text"] for e in raw_evidence)
        lean = _lean_from_text(combined_text)

        if lean > 0:
            signal = "POSITIVE"
        elif lean < 0:
            signal = "NEGATIVE"
        else:
            signal = "NEUTRAL"

        avg_relevance = sum(e["score"] for e in raw_evidence) / len(raw_evidence)
        confidence = round(min(0.9, 0.4 + avg_relevance * 0.5), 2)

        reasons = [
            f"{len(raw_evidence)} relevant document chunk(s) retrieved "
            f"(avg relevance {avg_relevance:.2f})."
        ]

        prompt = (
            f"Symbol: {symbol}\nQuestion: {query_text}\n"
            f"Retrieved document excerpts (ONLY use these, do not add outside facts): "
            f"{[e['text'][:300] for e in raw_evidence]}\n"
            f"Rule-based lean: {signal}\n"
            f"Write a 2-3 sentence fundamentals summary grounded strictly in the excerpts above, "
            f"and note you are citing specific documents/pages shown separately."
        )
        narration = await call_llm(
            prompt,
            system="You are a financial analyst who only reasons from the provided document excerpts "
                   "and never invents facts not present in them.",
        )

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            signal=signal,
            confidence=confidence,
            reasons=reasons,
            evidence=citations,
            metrics={"narration": narration, "avg_relevance": round(avg_relevance, 3)},
        )