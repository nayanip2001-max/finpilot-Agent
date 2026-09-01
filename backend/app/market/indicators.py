"""
Deterministic technical indicator calculations.

IMPORTANT (per engineering rules): the LLM never performs numerical
calculations. Everything here is plain pandas/numpy arithmetic; the LLM
layer (see agents/technical.py) only narrates these already-computed numbers.
"""
from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50.0)  # neutral RSI when undefined (flat/insufficient data)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def volatility(series: pd.Series, window: int = 20) -> pd.Series:
    """Annualized rolling volatility from daily returns."""
    returns = series.pct_change()
    return returns.rolling(window=window, min_periods=2).std() * np.sqrt(252)


def volume_anomaly(volume: pd.Series, window: int = 20) -> pd.Series:
    """How many standard deviations today's volume is from its rolling mean."""
    rolling_mean = volume.rolling(window=window, min_periods=2).mean()
    rolling_std = volume.rolling(window=window, min_periods=2).std().replace(0, np.nan)
    z = (volume - rolling_mean) / rolling_std
    return z.fillna(0.0)


def momentum(series: pd.Series, window: int = 10) -> pd.Series:
    """Rate of change over `window` periods, as a percentage."""
    return series.pct_change(periods=window) * 100


def compute_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute the full indicator set on an OHLCV DataFrame and return both the
    full series (for charting) and the latest scalar values (for the agent).
    """
    close = df["close"]
    volume = df["volume"]

    sma20 = sma(close, 20)
    sma50 = sma(close, 50)
    rsi14 = rsi(close, 14)
    macd_vals = macd(close)
    vol20 = volatility(close, 20)
    vol_anom = volume_anomaly(volume, 20)
    mom10 = momentum(close, 10)

    latest = {
        "close": float(close.iloc[-1]),
        "sma_20": float(sma20.iloc[-1]),
        "sma_50": float(sma50.iloc[-1]) if len(sma50.dropna()) else None,
        "rsi_14": round(float(rsi14.iloc[-1]), 2),
        "macd": round(float(macd_vals["macd"].iloc[-1]), 4),
        "macd_signal": round(float(macd_vals["signal"].iloc[-1]), 4),
        "macd_histogram": round(float(macd_vals["histogram"].iloc[-1]), 4),
        "volatility_annualized": round(float(vol20.iloc[-1]), 4) if not np.isnan(vol20.iloc[-1]) else None,
        "volume_anomaly_z": round(float(vol_anom.iloc[-1]), 2),
        "momentum_10d_pct": round(float(mom10.iloc[-1]), 2) if not np.isnan(mom10.iloc[-1]) else None,
        "price_vs_sma20_pct": round(((close.iloc[-1] - sma20.iloc[-1]) / sma20.iloc[-1]) * 100, 2),
    }

    series = {
        "dates": df["date"].astype(str).tolist(),
        "close": close.tolist(),
        "sma_20": sma20.tolist(),
        "sma_50": sma50.tolist(),
        "rsi_14": rsi14.tolist(),
    }

    return {"latest": latest, "series": series}