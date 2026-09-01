"""
ReplayMarketDataProvider: reads historical OHLCV CSVs from disk and serves
them as if they were a live feed. This satisfies the problem statement's
requirement to avoid depending on paid live-market APIs while still giving a
convincing "SIMULATED LIVE FEED" demo experience.

CSV files live at backend/data/market/{SYMBOL}.csv with columns:
date, open, high, low, close, volume
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd

from app.config import get_settings
from app.market.provider import MarketDataProvider, MarketSnapshot, MarketDataUnavailableError

logger = logging.getLogger("finpilot.market.replay")

settings = get_settings()


class ReplayMarketDataProvider(MarketDataProvider):
    def __init__(self, data_dir: str | None = None):
        self.data_dir = Path(data_dir or settings.market_data_path)
        self._cache: Dict[str, pd.DataFrame] = {}
        # Simulated "current position" pointer per symbol so /stream can advance
        # a cursor over history to feel live without needing a websocket.
        self._cursor: Dict[str, int] = {}

    # ---- internal helpers -------------------------------------------------

    def _load(self, symbol: str) -> pd.DataFrame:
        symbol = symbol.upper()
        if symbol in self._cache:
            return self._cache[symbol]

        path = self.data_dir / f"{symbol}.csv"
        if not path.exists():
            raise MarketDataUnavailableError(
                f"No market data file found for symbol '{symbol}' at {path}"
            )
        try:
            df = pd.read_csv(path, parse_dates=["date"])
            df = df.sort_values("date").reset_index(drop=True)
            required_cols = {"date", "open", "high", "low", "close", "volume"}
            missing = required_cols - set(df.columns.str.lower())
            if missing:
                raise MarketDataUnavailableError(
                    f"Market data file for '{symbol}' is missing columns: {missing}"
                )
        except Exception as exc:  # noqa: BLE001 - degraded-data path, never crash caller
            logger.error("Failed to load market data for %s: %s", symbol, exc)
            raise MarketDataUnavailableError(str(exc)) from exc

        self._cache[symbol] = df
        return df

    # ---- MarketDataProvider interface --------------------------------------

    def get_history(self, symbol: str, lookback: int = 200) -> pd.DataFrame:
        df = self._load(symbol)
        return df.tail(lookback).reset_index(drop=True)

    def get_latest(self, symbol: str) -> MarketSnapshot:
        df = self._load(symbol)
        row = df.iloc[-1]
        return MarketSnapshot(
            symbol=symbol.upper(),
            date=str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"]),
            is_simulated=True,
        )

    def list_symbols(self) -> List[str]:
        if not self.data_dir.exists():
            return []
        return sorted(p.stem.upper() for p in self.data_dir.glob("*.csv"))

    def is_live(self) -> bool:
        return False

    # ---- simulated streaming ------------------------------------------------

    def next_tick(self, symbol: str) -> MarketSnapshot:
        """
        Advance a per-symbol cursor through history and return that bar,
        wrapping around at the end. Used by GET /api/market/{symbol}/stream
        to emit a plausible "live" sequence from replayed historical data.
        """
        df = self._load(symbol)
        i = self._cursor.get(symbol.upper(), max(0, len(df) - 30))  # start near the end
        row = df.iloc[i % len(df)]
        self._cursor[symbol.upper()] = i + 1
        return MarketSnapshot(
            symbol=symbol.upper(),
            date=str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"]),
            is_simulated=True,
        )


# Module-level singleton so the cursor state persists across requests within one process.
replay_provider = ReplayMarketDataProvider()