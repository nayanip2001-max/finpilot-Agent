"""
Technical Analyst Agent.

Input: OHLCV market data + symbol.
Calculates SMA20/50, RSI, MACD, volatility, volume anomaly, momentum
PROGRAMMATICALLY (see app/market/indicators.py + signals.py) — never via LLM.
The LLM (mock or real) only narrates the already-computed numbers.
"""
from __future__ import annotations

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.market.indicators import compute_all_indicators
from app.market.provider import MarketDataProvider, MarketDataUnavailableError
from app.market.signals import classify_technical_signal
from app.utils.llm import call_llm


class TechnicalAgent(BaseAgent):
    name = "technical"
    purpose = (
        "Analyzes OHLCV price/volume data to classify short-term technical "
        "momentum using SMA20/50, RSI, MACD, volatility, volume anomaly, and "
        "10-day price momentum."
    )

    def __init__(self, market_provider: MarketDataProvider):
        self.market_provider = market_provider

    async def execute(self, symbol: str, **kwargs) -> AgentResult:
        try:
            df = self.market_provider.get_history(symbol, lookback=200)
        except MarketDataUnavailableError as exc:
            # Degraded-data path: never crash, return a clearly-marked degraded result.
            return AgentResult(
                agent=self.name,
                status=AgentStatus.DEGRADED,
                signal="UNKNOWN",
                confidence=0.0,
                reasons=[f"Technical market feed unavailable for {symbol}: {exc}. "
                         f"Using no data — confidence reduced to 0."],
                evidence=[],
                metrics={},
            )

        if len(df) < 5:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.DEGRADED,
                signal="UNKNOWN",
                confidence=0.1,
                reasons=["Insufficient market history to compute reliable indicators."],
            )

        indicators = compute_all_indicators(df)
        signal, confidence, reasons = classify_technical_signal(indicators["latest"])

        # LLM narration step (mock by default) — explains, does not calculate.
        prompt = (
            f"Symbol: {symbol}\nComputed indicators: {indicators['latest']}\n"
            f"Rule-based signal: {signal} (confidence {confidence})\n"
            f"Explain this technical signal in 2-3 sentences for a retail investor."
        )
        narration = await call_llm(prompt, system="You are a concise technical market analyst.")

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            signal=signal,
            confidence=confidence,
            reasons=reasons,
            evidence=[{"type": "computed_indicators", "source": "programmatic",
                       "detail": indicators["latest"]}],
            metrics={**indicators["latest"], "narration": narration, "chart_series": indicators["series"]},
        )