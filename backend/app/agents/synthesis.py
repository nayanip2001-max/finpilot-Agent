"""
Synthesis Agent.

Consumes structured outputs from Technical, Fundamental/RAG, Sentiment, and
Risk agents plus the user profile, and produces the final recommendation.

This agent explicitly reasons about HOW the signals interact (e.g. positive
market signals + over-concentrated risk => HOLD, not BUY) rather than just
repeating the individual agent outputs. It is rule-based/deterministic at
the decision-logic level (auditable), with LLM narration layered on top for
the human-readable summary.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.utils.llm import call_llm

# Points assigned per market-facing signal (technical + fundamental + sentiment)
DIRECTIONAL_POINTS = {
    "BULLISH": 1, "POSITIVE": 1, "ROOM_TO_ADD": 1,
    "NEUTRAL": 0, "AT_CAPACITY": 0, "UNKNOWN": 0,
    "BEARISH": -1, "NEGATIVE": -1, "OVER_CONCENTRATED": -1,
}


class SynthesisAgent(BaseAgent):
    name = "synthesis"
    purpose = (
        "Combines technical, fundamental, sentiment, and risk agent outputs "
        "with the user's profile into a single explainable recommendation, "
        "explicitly reasoning about how the signals interact rather than "
        "simply restating them."
    )

    async def execute(
        self,
        technical: AgentResult,
        fundamental: AgentResult,
        sentiment: AgentResult,
        risk: AgentResult,
        user: Dict[str, Any],
        symbol: str,
        question: str | None = None,
        **kwargs,
    ) -> AgentResult:
        agent_results = {"technical": technical, "fundamental": fundamental,
                          "sentiment": sentiment, "risk": risk}

        degraded = any(r.status.value in ("DEGRADED", "FAILED") for r in agent_results.values())

        # --- market-facing consensus (technical + fundamental + sentiment) ---
        market_agents = [technical, fundamental, sentiment]
        available_market = [a for a in market_agents if a.status.value != "FAILED"]
        market_score = 0.0
        market_weight = 0.0
        for a in available_market:
            pts = DIRECTIONAL_POINTS.get(a.signal, 0)
            market_score += pts * a.confidence
            market_weight += a.confidence
        market_lean = (market_score / market_weight) if market_weight else 0.0  # -1..1

        signals_seen = {a.agent: a.signal for a in market_agents}
        conflicting = len(set(v for v in signals_seen.values() if v not in (None, "UNKNOWN"))) >= 2 and \
            (("BULLISH" in signals_seen.values() or "POSITIVE" in signals_seen.values()) and
             ("BEARISH" in signals_seen.values() or "NEGATIVE" in signals_seen.values()))

        # --- risk gate: risk agent can cap how far market enthusiasm is allowed to go ---
        risk_signal = risk.signal
        reasons: List[str] = []
        risks: List[str] = []
        what_would_change: List[str] = []

        if risk_signal == "OVER_CONCENTRATED":
            recommendation = "REDUCE" if market_lean < -0.1 else "HOLD"
            reasons.append(
                "Market signals were factored in, but this user is already over-concentrated in "
                f"{symbol} relative to their risk profile's comfortable ceiling, which caps the recommendation."
            )
            risks.append("Portfolio concentration risk exceeds comfort threshold for this user.")
            what_would_change.append("Reducing existing exposure elsewhere to free up concentration headroom.")
        elif market_lean > 0.35 and risk_signal == "ROOM_TO_ADD":
            recommendation = "BUY"
            reasons.append(
                "Technical, fundamental, and sentiment signals are net positive, and this user has "
                "both risk appetite and portfolio headroom to increase exposure."
            )
        elif market_lean < -0.35:
            recommendation = "AVOID" if risk_signal != "ROOM_TO_ADD" else "REDUCE"
            reasons.append("Market signals are net negative; new or existing exposure is not favored right now.")
            risks.append("Negative technical/fundamental/sentiment signals increase downside risk.")
        else:
            recommendation = "HOLD"
            reasons.append(
                "Market signals are mixed or moderately positive/negative, not strong enough on their own "
                "to justify changing this user's position size."
            )

        if conflicting:
            reasons.append(
                "Technical and fundamental/sentiment signals disagree — confidence has been reduced "
                "and the recommendation leans conservative until signals align."
            )
            what_would_change.append("Alignment between technical momentum and fundamental/sentiment direction.")

        if degraded:
            reasons.append(
                "One or more agents returned degraded or missing data; this recommendation's confidence "
                "has been lowered accordingly and no missing evidence was fabricated."
            )
            risks.append("Recommendation is based on partial data due to a degraded input source.")

        # --- confidence: weighted agent confidence, penalized by conflict/degradation ---
        confidences = [a.confidence for a in agent_results.values() if a.status.value != "FAILED"]
        base_confidence = sum(confidences) / len(confidences) if confidences else 0.3
        penalty = (0.15 if conflicting else 0) + (0.15 if degraded else 0)
        final_confidence = round(max(0.1, min(0.95, base_confidence - penalty)), 2)

        # --- agent consensus summary for the UI ---
        agent_consensus = {
            name: {"signal": r.signal, "confidence": r.confidence, "status": r.status.value}
            for name, r in agent_results.items()
        }

        # --- evidence: pass through fundamental agent's citations (only real RAG-backed evidence) ---
        evidence = fundamental.evidence

        # --- reasoning trace: step-by-step, concise, user-facing (no hidden chain-of-thought) ---
        reasoning_trace = [
            {"step": 1, "agent": "user_profile", "decision": user.get("risk_profile"),
             "confidence": None, "reason": f"Loaded profile for {user.get('name', user.get('id'))}."},
            {"step": 2, "agent": "technical", "decision": technical.signal,
             "confidence": technical.confidence, "reason": technical.reasons[0] if technical.reasons else ""},
            {"step": 3, "agent": "fundamental", "decision": fundamental.signal,
             "confidence": fundamental.confidence, "reason": fundamental.reasons[0] if fundamental.reasons else ""},
            {"step": 4, "agent": "sentiment", "decision": sentiment.signal,
             "confidence": sentiment.confidence, "reason": sentiment.reasons[0] if sentiment.reasons else ""},
            {"step": 5, "agent": "risk", "decision": risk.signal,
             "confidence": risk.confidence, "reason": risk.reasons[0] if risk.reasons else ""},
            {"step": 6, "agent": "synthesis", "decision": recommendation,
             "confidence": final_confidence, "reason": reasons[0] if reasons else ""},
        ]

        summary_prompt = (
            f"Symbol: {symbol}\nUser question: {question or 'Should I adjust my position?'}\n"
            f"Agent consensus: {agent_consensus}\nDecision-logic reasons: {reasons}\n"
            f"Final recommendation: {recommendation} (confidence {final_confidence})\n"
            f"Write a concise 2-3 sentence summary for the investor explaining this recommendation."
        )
        narration = await call_llm(
            summary_prompt,
            system="You are a synthesis agent for a multi-agent investment research desk. "
                   "Explain the final call plainly, referencing how the signals interacted.",
        )

        return AgentResult(
            agent=self.name,
            status=AgentStatus.DEGRADED if degraded else AgentStatus.SUCCESS,
            signal=recommendation,
            confidence=final_confidence,
            reasons=reasons,
            evidence=evidence,
            metrics={
                "narration": narration,
                "market_lean": round(market_lean, 3),
                "conflicting_signals": conflicting,
                "degraded": degraded,
                "agent_consensus": agent_consensus,
                "risks": risks,
                "what_would_change_decision": what_would_change,
                "reasoning_trace": reasoning_trace,
            },
        )