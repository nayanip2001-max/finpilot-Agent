"""
Base agent abstraction shared by every specialized agent
(technical, fundamental/RAG, sentiment, risk, synthesis).

Every agent:
 - declares name/purpose
 - declares input/output as typed Pydantic schemas (see api/schemas)
 - implements async execute()
 - always returns an AgentResult, even on failure (status=FAILED),
   so one failed agent never crashes the whole orchestration.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("finpilot.agents")


class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


@dataclass
class AgentResult:
    agent: str
    status: AgentStatus
    signal: Optional[str] = None          # e.g. BULLISH / POSITIVE / HOLD-lean, agent-specific
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "status": self.status.value,
            "signal": self.signal,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "evidence": self.evidence,
            "metrics": self.metrics,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


class BaseAgent(ABC):
    name: str = "base"
    purpose: str = "Abstract base agent"

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        """Run the agent's logic and return a structured AgentResult."""
        raise NotImplementedError

    async def run_safe(self, **kwargs) -> AgentResult:
        """
        Wrapper that times execution and guarantees a well-formed AgentResult
        is returned even if the underlying agent raises. This is what the
        orchestrator calls, satisfying the "one failed agent must not crash
        the analysis" requirement.
        """
        start = time.perf_counter()
        try:
            result = await self.execute(**kwargs)
            result.latency_ms = int((time.perf_counter() - start) * 1000)
            return result
        except Exception as exc:  # noqa: BLE001 - intentional broad catch at agent boundary
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.exception("Agent '%s' failed: %s", self.name, exc)
            return AgentResult(
                agent=self.name,
                status=AgentStatus.FAILED,
                confidence=0.0,
                reasons=[f"Agent failed: {exc}"],
                error=str(exc),
                latency_ms=latency_ms,
            )