from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.metrics.service import get_recommendation, list_metrics

router = APIRouter()


@router.get("/api/metrics")
async def get_metrics(symbol: Optional[str] = None, db: Session = Depends(get_db)):
    rows = list_metrics(db, symbol=symbol)
    return {
        "metrics": [
            {
                "run_id": r.run_id,
                "symbol": r.symbol,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                "metadata": r.metadata_json,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/api/metrics/{symbol}")
async def get_metrics_for_symbol(symbol: str, db: Session = Depends(get_db)):
    rows = list_metrics(db, symbol=symbol)
    return {
        "symbol": symbol.upper(),
        "metrics": [
            {"metric_name": r.metric_name, "metric_value": r.metric_value, "created_at": r.created_at.isoformat()}
            for r in rows
        ],
    }


@router.get("/api/recommendations/{run_id}")
async def get_recommendation_by_id(run_id: str, db: Session = Depends(get_db)):
    rec = get_recommendation(db, run_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation for run '{run_id}' not found")
    return {
        "run_id": rec.run_id,
        "symbol": rec.symbol,
        "recommendation": rec.recommendation,
        "confidence": rec.confidence,
        "summary": rec.summary,
        "reasons": rec.reasons_json,
        "risks": rec.risks_json,
        "evidence": rec.evidence_json,
        "reasoning_trace": rec.reasoning_trace_json,
        "degraded": rec.degraded,
        "latency_ms": rec.latency_ms,
        "created_at": rec.created_at.isoformat(),
    }


@router.get("/api/reasoning/{run_id}")
async def get_reasoning_trace(run_id: str, db: Session = Depends(get_db)):
    rec = get_recommendation(db, run_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Reasoning trace for run '{run_id}' not found")
    return {"run_id": rec.run_id, "reasoning_trace": rec.reasoning_trace_json}