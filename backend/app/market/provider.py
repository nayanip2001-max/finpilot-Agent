"""
MarketDataProvider abstraction.

The rest of the app talks to `MarketDataProvider`, never to a CSV file or a
specific vendor SDK directly. This lets us swap ReplayMarketDataProvider for
a real LiveMarketDataProvider later without touching agents/API routes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd


class MarketDataUnavailableError(Exception):
    """Raised when a provider cannot return data for a symbol (degraded-data path)."""


@dataclass
class MarketSnapshot:
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    is_simulated: bool = True


class MarketDataProvider(ABC):
    """Abstract interface every market data source must implement."""

    @abstractmethod
    def get_history(self, symbol: str, lookback: int = 200) -> pd.DataFrame:
        """Return an OHLCV DataFrame indexed by date, most-recent last."""
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, symbol: str) -> MarketSnapshot:
        """Return the most recent bar for a symbol."""
        raise NotImplementedError

    @abstractmethod
    def list_symbols(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def is_live(self) -> bool:
        """False for replay/simulated providers. Used by the UI to label data provenance."""
        raise NotImplementedError


class LiveMarketDataProvider(MarketDataProvider):
    """
    Placeholder interface for a future real-time provider (e.g. NSE feed, broker API).

    NOT implemented for the hackathon MVP per the problem statement's constraint
    against depending on paid APIs for the core demo. Wire a real implementation
    here later (e.g. websocket ticks -> DataFrame) without touching any agent code.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def get_history(self, symbol: str, lookback: int = 200) -> pd.DataFrame:
        raise NotImplementedError("Plug in a real market data vendor here.")

    def get_latest(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError("Plug in a real market data vendor here.")

    def list_symbols(self) -> List[str]:
        raise NotImplementedError

    def is_live(self) -> bool:
        return True