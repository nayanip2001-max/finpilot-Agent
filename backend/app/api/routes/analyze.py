from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import Orchestrator
from app.api.schemas.analyze import AnalyzeRequest
from app.database.session import get_db
from app.market.replay import replay_provider
from app.metrics.service import save_analysis_run
from app.users.service import user_service

router = APIRouter()
orchestrator = Orchestrator(market_provider=replay_provider)


@router.post("/api/analyze")
async def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    user = user_service.get_user(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{payload.user_id}' not found")

    result = await orchestrator.analyze(user=user, symbol=payload.symbol, question=payload.question)
    save_analysis_run(db, user_id=payload.user_id, question=payload.question, result=result)
    return result


@router.post("/api/analyze/{symbol}")
async def analyze_symbol(symbol: str, payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """Same as POST /api/analyze but with the symbol in the path (payload.symbol is overridden)."""
    payload.symbol = symbol
    return await analyze(payload, db)