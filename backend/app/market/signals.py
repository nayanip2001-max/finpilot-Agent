"""
Deterministic rule-based classification of computed indicators into a
BULLISH / NEUTRAL / BEARISH signal + confidence + human-readable reasons.

This is intentionally NOT an LLM call: signal classification must be
reproducible and auditable. The LLM (mock or real) is only used downstream
to phrase natural-language narration around these already-decided facts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def classify_technical_signal(latest: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    """
    Simple, transparent scoring rule:
      +1 bullish point for price > SMA20, SMA20 > SMA50, RSI in healthy range,
         positive MACD histogram, positive momentum.
      -1 for the inverse of each.
    Score is mapped to a signal label and confidence.
    """
    reasons: List[str] = []
    score = 0
    total_checks = 0

    close = latest["close"]
    sma20 = latest.get("sma_20")
    sma50 = latest.get("sma_50")
    rsi14 = latest.get("rsi_14")
    macd_hist = latest.get("macd_histogram")
    momentum = latest.get("momentum_10d_pct")
    vol_anom = latest.get("volume_anomaly_z")

    if sma20 is not None:
        total_checks += 1
        if close > sma20:
            score += 1
            reasons.append(f"Price ({close:.2f}) is above SMA20 ({sma20:.2f}).")
        else:
            score -= 1
            reasons.append(f"Price ({close:.2f}) is below SMA20 ({sma20:.2f}).")

    if sma20 is not None and sma50 is not None:
        total_checks += 1
        if sma20 > sma50:
            score += 1
            reasons.append("SMA20 is above SMA50 (short-term uptrend).")
        else:
            score -= 1
            reasons.append("SMA20 is below SMA50 (short-term downtrend).")

    if rsi14 is not None:
        total_checks += 1
        if rsi14 >= 70:
            score -= 1
            reasons.append(f"RSI ({rsi14:.1f}) is in overbought territory.")
        elif rsi14 <= 30:
            score -= 1
            reasons.append(f"RSI ({rsi14:.1f}) is in oversold territory.")
        elif rsi14 >= 50:
            score += 1
            reasons.append(f"RSI ({rsi14:.1f}) shows healthy bullish momentum.")
        else:
            reasons.append(f"RSI ({rsi14:.1f}) is neutral-to-weak.")

    if macd_hist is not None:
        total_checks += 1
        if macd_hist > 0:
            score += 1
            reasons.append("MACD histogram is positive (bullish crossover).")
        else:
            score -= 1
            reasons.append("MACD histogram is negative (bearish crossover).")

    if momentum is not None:
        total_checks += 1
        if momentum > 1:
            score += 1
            reasons.append(f"10-day momentum is positive ({momentum:.2f}%).")
        elif momentum < -1:
            score -= 1
            reasons.append(f"10-day momentum is negative ({momentum:.2f}%).")
        else:
            reasons.append(f"10-day momentum is flat ({momentum:.2f}%).")

    if vol_anom is not None and abs(vol_anom) >= 2:
        reasons.append(f"Volume anomaly detected (z={vol_anom:.2f}) — unusual trading activity.")

    if total_checks == 0:
        return "NEUTRAL", 0.3, ["Insufficient indicator data to classify a signal."]

    normalized = score / total_checks  # range roughly [-1, 1]
    confidence = round(min(0.95, max(0.35, 0.55 + abs(normalized) * 0.4)), 2)

    if normalized > 0.2:
        signal = "BULLISH"
    elif normalized < -0.2:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    return signal, confidence, reasons