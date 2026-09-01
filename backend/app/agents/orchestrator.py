"""
Orchestrator: coordinates the full agent pipeline for one /api/analyze call.

Technical, Fundamental, and Sentiment agents run CONCURRENTLY via
asyncio.gather. Risk runs after (it needs portfolio/allocation numbers that
don't depend on the other three). Synthesis runs last, consuming all
structured outputs. A failure in any one agent is caught by BaseAgent.run_safe
and surfaced as a FAILED AgentResult rather than raising.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict

from app.agents.fundamental import FundamentalAgent
from app.agents.risk import RiskAgent
from app.agents.sentiment import SentimentAgent
from app.agents.synthesis import SynthesisAgent
from app.agents.technical import TechnicalAgent
from app.market.indicators import compute_all_indicators
from app.market.provider import MarketDataProvider, MarketDataUnavailableError
from app.portfolio.service import compute_allocation_pct


class Orchestrator:
    def __init__(self, market_provider: MarketDataProvider):
        self.market_provider = market_provider
        self.technical_agent = TechnicalAgent(market_provider)
        self.fundamental_agent = FundamentalAgent()
        self.sentiment_agent = SentimentAgent()
        self.risk_agent = RiskAgent()
        self.synthesis_agent = SynthesisAgent()

    async def analyze(self, user: Dict[str, Any], symbol: str, question: str | None = None) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        start = time.perf_counter()

        # --- Phase 1: Technical, Fundamental, Sentiment run CONCURRENTLY ---
        technical_task = self.technical_agent.run_safe(symbol=symbol)
        fundamental_task = self.fundamental_agent.run_safe(symbol=symbol, question=question)
        sentiment_task = self.sentiment_agent.run_safe(symbol=symbol)

        technical, fundamental, sentiment = await asyncio.gather(
            technical_task, fundamental_task, sentiment_task
        )

        # --- Phase 2: Risk agent (needs portfolio + volatility context) ---
        portfolio = user.get("portfolio", {})
        allocation_pct = compute_allocation_pct(portfolio, symbol)
        stock_volatility = technical.metrics.get("volatility_annualized")

        risk = await self.risk_agent.run_safe(
            user=user,
            current_allocation_pct=allocation_pct,
            stock_volatility=stock_volatility,
        )

        # --- Phase 3: Synthesis ---
        synthesis = await self.synthesis_agent.run_safe(
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
            risk=risk,
            user=user,
            symbol=symbol,
            question=question,
        )

        total_latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "run_id": run_id,
            "symbol": symbol,
            "recommendation": synthesis.signal,
            "confidence": synthesis.confidence,
            "summary": synthesis.metrics.get("narration"),
            "reasons": synthesis.reasons,
            "risks": synthesis.metrics.get("risks", []),
            "what_would_change_decision": synthesis.metrics.get("what_would_change_decision", []),
            "agent_consensus": synthesis.metrics.get("agent_consensus", {}),
            "evidence": synthesis.evidence,
            "reasoning_trace": synthesis.metrics.get("reasoning_trace", []),
            "agents": {
                "technical": technical.to_dict(),
                "fundamental": fundamental.to_dict(),
                "sentiment": sentiment.to_dict(),
                "risk": risk.to_dict(),
                "synthesis": synthesis.to_dict(),
            },
            "degraded": synthesis.metrics.get("degraded", False),
            "latency_ms": total_latency_ms,
        }