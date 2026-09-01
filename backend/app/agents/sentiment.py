"""
Sentiment Agent.

For the MVP, sentiment is derived from a small curated/synthetic news dataset
(backend/data/news/{symbol}.json). Each headline is scored with a simple
lexicon-based rule (deterministic, auditable) and then narrated by the LLM
layer. Real sources (news APIs, transcripts) can replace the JSON loader
later without changing this agent's output contract.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.config import get_settings
from app.utils.llm import call_llm

logger = logging.getLogger("finpilot.agents.sentiment")

POSITIVE_WORDS = {
    "beats", "beat", "growth", "record", "upgrade", "upgraded", "strong", "surge",
    "profit", "expansion", "outperform", "rally", "raised", "positive", "robust",
    "wins", "won", "gain", "gains", "bullish", "improve", "improved",
}
NEGATIVE_WORDS = {
    "misses", "miss", "downgrade", "downgraded", "weak", "decline", "declines",
    "loss", "losses", "lawsuit", "probe", "investigation", "cut", "cuts",
    "bearish", "concern", "concerns", "fall", "falls", "slump", "warning",
    "delay", "delayed", "fraud", "penalty",
}


def _score_headline(text: str) -> int:
    words = {w.strip(".,!?").lower() for w in text.split()}
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    return pos - neg


class SentimentAgent(BaseAgent):
    name = "sentiment"
    purpose = (
        "Scores a curated set of news headlines / transcript snippets for a "
        "symbol to classify overall market sentiment as POSITIVE, NEUTRAL, or NEGATIVE."
    )

    def __init__(self, news_dir: str | None = None):
        settings = get_settings()
        self.news_dir = Path(news_dir or settings.news_data_path)

    def _load_news(self, symbol: str) -> List[Dict[str, Any]]:
        path = self.news_dir / f"{symbol.upper()}.json"
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to parse news file for %s: %s", symbol, exc)
            return []

    async def execute(self, symbol: str, **kwargs) -> AgentResult:
        headlines = self._load_news(symbol)

        if not headlines:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.DEGRADED,
                signal="NEUTRAL",
                confidence=0.2,
                reasons=[f"No news dataset found for {symbol}. Defaulting to NEUTRAL with low confidence."],
                evidence=[],
            )

        scores = []
        reasons: List[str] = []
        evidence: List[Dict[str, Any]] = []
        for item in headlines:
            headline = item.get("headline", "")
            s = _score_headline(headline)
            scores.append(s)
            evidence.append({
                "type": "synthetic_news" if item.get("synthetic", True) else "real_news",
                "headline": headline,
                "date": item.get("date"),
                "source": item.get("source", "SYNTHETIC DEMO DATA"),
                "score": s,
            })

        total = sum(scores)
        avg = total / len(scores)

        if avg > 0.3:
            signal = "POSITIVE"
        elif avg < -0.3:
            signal = "NEGATIVE"
        else:
            signal = "NEUTRAL"

        confidence = round(min(0.9, 0.4 + min(abs(avg), 3) * 0.15), 2)

        pos_count = sum(1 for s in scores if s > 0)
        neg_count = sum(1 for s in scores if s < 0)
        neu_count = len(scores) - pos_count - neg_count
        reasons.append(
            f"{len(headlines)} headlines analyzed: {pos_count} positive, "
            f"{neg_count} negative, {neu_count} neutral (net score {total})."
        )
        if any(not h.get("synthetic", True) is False for h in headlines):
            reasons.append("Dataset is SYNTHETIC DEMO DATA unless individually marked otherwise.")

        prompt = (
            f"Symbol: {symbol}\nHeadlines and scores: {evidence}\n"
            f"Rule-based sentiment: {signal} (confidence {confidence})\n"
            f"Summarize the sentiment picture in 2-3 sentences."
        )
        narration = await call_llm(prompt, system="You are a concise financial sentiment analyst.")

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            signal=signal,
            confidence=confidence,
            reasons=reasons,
            evidence=evidence,
            metrics={"narration": narration, "avg_score": avg, "headline_count": len(headlines)},
        )