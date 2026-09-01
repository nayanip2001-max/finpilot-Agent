import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyze, health, market, metrics, rag, users
from app.config import get_settings
from app.database.session import init_db

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("finpilot.main")

app = FastAPI(
    title="FinPilot AI",
    description="A multi-agent AI research desk for every retail investor.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(market.router, tags=["market"])
app.include_router(users.router, tags=["users"])
app.include_router(rag.router, tags=["rag"])
app.include_router(analyze.router, tags=["analyze"])
app.include_router(metrics.router, tags=["metrics"])


@app.on_event("startup")
async def on_startup():
    logger.info("Starting FinPilot AI backend (LLM_MODE=%s, environment=%s)",
                settings.llm_mode, settings.environment)
    init_db()
    logger.info("Database initialized.")


@app.get("/")
async def root():
    return {
        "name": "FinPilot AI",
        "tagline": "A multi-agent AI research desk for every retail investor.",
        "docs": "/docs",
        "llm_mode": settings.llm_mode,
    }