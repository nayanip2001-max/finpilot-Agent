"""
SQLAlchemy models for FinPilot AI.

Tables:
 - agent_runs          : one row per agent execution within an /api/analyze call
 - recommendations     : one row per synthesized final recommendation
 - performance_metrics : measurable metrics captured per session/run
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, Integer

from app.database.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, index=True, nullable=False)  # groups agents under one /analyze call
    agent_name = Column(String, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    status = Column(String, default="SUCCESS")  # SUCCESS | FAILED | DEGRADED
    signal = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    latency_ms = Column(Integer, default=0)
    output_json = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, index=True, unique=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    question = Column(String, nullable=True)
    recommendation = Column(String, nullable=False)  # BUY | HOLD | REDUCE | AVOID
    confidence = Column(Float, nullable=False)
    summary = Column(String, nullable=True)
    reasons_json = Column(JSON, nullable=True)
    risks_json = Column(JSON, nullable=True)
    what_would_change_json = Column(JSON, nullable=True)
    agent_consensus_json = Column(JSON, nullable=True)
    evidence_json = Column(JSON, nullable=True)
    reasoning_trace_json = Column(JSON, nullable=True)
    degraded = Column(Boolean, default=False)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, index=True, nullable=True)
    symbol = Column(String, index=True, nullable=True)
    metric_name = Column(String, nullable=False)  # e.g. "agent_latency_ms", "signal_accuracy", "concentration_risk"
    metric_value = Column(Float, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)