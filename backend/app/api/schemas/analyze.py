from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., examples=["user_001"])
    symbol: str = Field(..., examples=["RELIANCE"])
    question: Optional[str] = Field(None, examples=["Should I increase my position?"])


class AnalyzeResponse(BaseModel):
    run_id: str
    symbol: str
    recommendation: str
    confidence: float
    summary: Optional[str] = None
    reasons: List[str] = []
    risks: List[str] = []
    what_would_change_decision: List[str] = []
    agent_consensus: Dict[str, Any] = {}
    evidence: List[Dict[str, Any]] = []
    reasoning_trace: List[Dict[str, Any]] = []
    agents: Dict[str, Any] = {}
    degraded: bool = False
    latency_ms: int = 0


class RagSearchRequest(BaseModel):
    query: str
    company: Optional[str] = None
    top_k: int = 5