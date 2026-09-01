from fastapi import APIRouter, HTTPException

from app.market.indicators import compute_all_indicators
from app.market.provider import MarketDataUnavailableError
from app.market.replay import replay_provider

router = APIRouter()

# Friendly display names for the demo symbol universe.
STOCK_META = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "HDFCBANK": "HDFC Bank",
    "INFY": "Infosys",
    "ICICIBANK": "ICICI Bank",
}


@router.get("/api/stocks")
async def list_stocks():
    symbols = replay_provider.list_symbols()
    return {
        "stocks": [
            {"symbol": s, "name": STOCK_META.get(s, s)} for s in symbols
        ]
    }


@router.get("/api/market/{symbol}")
async def get_market_history(symbol: str, lookback: int = 200):
    try:
        df = replay_provider.get_history(symbol, lookback=lookback)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    indicators = compute_all_indicators(df)
    return {
        "symbol": symbol.upper(),
        "is_simulated": True,
        "data_status": "SIMULATED LIVE FEED",
        "history": df.assign(date=df["date"].astype(str)).to_dict(orient="records"),
        "indicators": indicators,
    }


@router.get("/api/market/{symbol}/latest")
async def get_market_latest(symbol: str):
    try:
        snapshot = replay_provider.get_latest(symbol)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {**snapshot.__dict__, "data_status": "SIMULATED LIVE FEED"}


@router.get("/api/market/{symbol}/stream")
async def stream_market(symbol: str):
    """
    Returns the NEXT simulated tick for a symbol by advancing a server-side
    cursor over historical data. The frontend polls this endpoint to create
    the appearance of a live feed. Clearly not real-time data.
    """
    try:
        snapshot = replay_provider.next_tick(symbol)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {**snapshot.__dict__, "data_status": "SIMULATED LIVE FEED"}