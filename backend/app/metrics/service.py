"""
Persists agent runs, final recommendations, and performance metrics.
Backs GET /api/metrics and GET /api/reasoning/{id}.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database.models import AgentRun, PerformanceMetric, Recommendation


def save_analysis_run(db: Session, user_id: str, question: Optional[str], result: Dict[str, Any]) -> None:
    run_id = result["run_id"]
    symbol = result["symbol"]

    for agent_name, agent_data in result["agents"].items():
        db.add(AgentRun(
            run_id=run_id,
            agent_name=agent_name,
            symbol=symbol,
            status=agent_data.get("status", "SUCCESS"),
            signal=agent_data.get("signal"),
            confidence=agent_data.get("confidence"),
            latency_ms=agent_data.get("latency_ms", 0),
            output_json=agent_data,
            error=agent_data.get("error"),
        ))
        db.add(PerformanceMetric(
            run_id=run_id, symbol=symbol,
            metric_name="agent_response_latency_ms",
            metric_value=float(agent_data.get("latency_ms", 0)),
            metadata_json={"agent": agent_name},
        ))

    db.add(Recommendation(
        run_id=run_id,
        user_id=user_id,
        symbol=symbol,
        question=question,
        recommendation=result["recommendation"],
        confidence=result["confidence"],
        summary=result.get("summary"),
        reasons_json=result.get("reasons"),
        risks_json=result.get("risks"),
        what_would_change_json=result.get("what_would_change_decision"),
        agent_consensus_json=result.get("agent_consensus"),
        evidence_json=result.get("evidence"),
        reasoning_trace_json=result.get("reasoning_trace"),
        degraded=bool(result.get("degraded", False)),
        latency_ms=result.get("latency_ms", 0),
    ))

    db.add(PerformanceMetric(
        run_id=run_id, symbol=symbol,
        metric_name="total_pipeline_latency_ms",
        metric_value=float(result.get("latency_ms", 0)),
    ))

    db.commit()


def get_recommendation(db: Session, run_id: str) -> Optional[Recommendation]:
    return db.query(Recommendation).filter(Recommendation.run_id == run_id).first()


def list_metrics(db: Session, symbol: Optional[str] = None, limit: int = 100) -> List[PerformanceMetric]:
    q = db.query(PerformanceMetric)
    if symbol:
        q = q.filter(PerformanceMetric.symbol == symbol.upper())
    return q.order_by(PerformanceMetric.created_at.desc()).limit(limit).all()