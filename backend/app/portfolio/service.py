"""
Portfolio calculations: allocation %, concentration score, P&L.
All computed programmatically (never by the LLM) so numbers stay auditable.
"""
from __future__ import annotations

from typing import Any, Dict, List


def compute_allocation_pct(portfolio: Dict[str, Any], symbol: str) -> float:
    holdings: List[Dict[str, Any]] = portfolio.get("holdings", [])
    total_value = sum(h.get("current_value", 0) for h in holdings) or 1e-9
    for h in holdings:
        if h.get("symbol", "").upper() == symbol.upper():
            return round((h.get("current_value", 0) / total_value) * 100, 2)
    return 0.0


def compute_concentration_score(portfolio: Dict[str, Any]) -> float:
    """
    Herfindahl-style concentration score in [0, 1]: sum of squared allocation
    shares. Higher = more concentrated in fewer names.
    """
    holdings: List[Dict[str, Any]] = portfolio.get("holdings", [])
    total_value = sum(h.get("current_value", 0) for h in holdings) or 1e-9
    shares = [(h.get("current_value", 0) / total_value) for h in holdings]
    return round(sum(s * s for s in shares), 4)


def enrich_portfolio(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    holdings: List[Dict[str, Any]] = portfolio.get("holdings", [])
    total_value = sum(h.get("current_value", 0) for h in holdings)
    total_cost = sum(h.get("cost_basis", h.get("current_value", 0)) for h in holdings)
    daily_pnl = sum(h.get("daily_pnl", 0) for h in holdings)

    enriched_holdings = []
    for h in holdings:
        allocation_pct = round((h.get("current_value", 0) / total_value) * 100, 2) if total_value else 0.0
        enriched_holdings.append({**h, "allocation_pct": allocation_pct})

    return {
        "holdings": sorted(enriched_holdings, key=lambda h: h["allocation_pct"], reverse=True),
        "total_value": round(total_value, 2),
        "total_pnl": round(total_value - total_cost, 2),
        "daily_pnl": round(daily_pnl, 2),
        "concentration_score": compute_concentration_score(portfolio),
    }