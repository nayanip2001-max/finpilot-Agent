"""
Risk / Personalization Agent.

This is the agent responsible for the core personalization requirement:
identical market signals must be able to produce different outputs for
different users based on risk profile, current allocation/concentration,
and behavioral history.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import AgentResult, AgentStatus, BaseAgent

RISK_TOLERANCE_BY_PROFILE = {
    "CONSERVATIVE": 0.25,
    "MODERATE": 0.5,
    "AGGRESSIVE": 0.8,
}

# Allocation ceiling (% of portfolio) each profile is comfortable holding in one name.
CONCENTRATION_CEILING = {
    "CONSERVATIVE": 15.0,
    "MODERATE": 25.0,
    "AGGRESSIVE": 40.0,
}


class RiskAgent(BaseAgent):
    name = "risk"
    purpose = (
        "Evaluates portfolio concentration, stock volatility, and the user's "
        "stored risk profile/behavioral history to produce a personalized risk "
        "lean, independent of the raw market signal."
    )

    async def execute(
        self,
        user: Dict[str, Any],
        current_allocation_pct: float,
        stock_volatility: float | None,
        **kwargs,
    ) -> AgentResult:
        profile = (user.get("risk_profile") or "MODERATE").upper()
        behavior = user.get("behavior", {})
        risk_aversion = behavior.get("risk_aversion", 0.5)

        ceiling = CONCENTRATION_CEILING.get(profile, 25.0)
        tolerance = RISK_TOLERANCE_BY_PROFILE.get(profile, 0.5)

        reasons: List[str] = [
            f"User risk profile: {profile} (stored risk_aversion={risk_aversion})."
        ]

        headroom_pct = ceiling - current_allocation_pct
        reasons.append(
            f"Current allocation to this stock is {current_allocation_pct:.1f}% of portfolio; "
            f"comfortable ceiling for a {profile.title()} profile is ~{ceiling:.0f}%."
        )

        if stock_volatility is not None:
            reasons.append(f"Stock's annualized volatility: {stock_volatility:.2%}.")
            vol_penalty = min(0.3, stock_volatility)  # high-vol stocks reduce comfort further
        else:
            vol_penalty = 0.1
            reasons.append("Volatility data unavailable — applying a conservative default penalty.")

        # Compute a normalized "risk lean" score in [-1, 1]:
        #  positive => room / appetite to add exposure
        #  negative => already over-concentrated / low risk tolerance for more
        headroom_component = max(-1.0, min(1.0, headroom_pct / ceiling)) if ceiling else 0
        appetite_component = (tolerance - 0.5) * 2  # -1..1, aggressive users skew positive
        score = (headroom_component * 0.6) + (appetite_component * 0.4) - vol_penalty

        if score > 0.15:
            lean = "ROOM_TO_ADD"
        elif score < -0.15:
            lean = "OVER_CONCENTRATED"
        else:
            lean = "AT_CAPACITY"

        confidence = round(min(0.9, 0.5 + abs(score) * 0.3), 2)

        if lean == "OVER_CONCENTRATED":
            reasons.append(
                f"Adding further exposure would push allocation meaningfully past this user's "
                f"comfortable concentration ceiling."
            )
        elif lean == "ROOM_TO_ADD":
            reasons.append("User has headroom under their concentration ceiling and sufficient risk appetite.")
        else:
            reasons.append("User is near their comfortable capacity for this position.")

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            signal=lean,
            confidence=confidence,
            reasons=reasons,
            evidence=[{"type": "user_profile", "source": "synthetic_user_store",
                       "detail": {"risk_profile": profile, "behavior": behavior}}],
            metrics={
                "current_allocation_pct": current_allocation_pct,
                "concentration_ceiling_pct": ceiling,
                "risk_score": round(score, 3),
            },
        )