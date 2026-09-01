"""
Central configuration for FinPilot AI backend.

All values are overridable via environment variables / .env file.
Nothing here should ever contain a hard-coded secret.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # --- LLM ---
    llm_mode: str = "mock"  # "mock" | "real"
    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"

    # --- Database ---
    database_url: str = f"sqlite:///{BASE_DIR}/finpilot.db"

    # --- RAG ---
    vector_db_path: str = str(BASE_DIR / "data" / "vector_store")
    embedding_model: str = "all-MiniLM-L6-v2"
    documents_path: str = str(BASE_DIR / "data" / "documents")

    # --- Market data ---
    market_data_path: str = str(BASE_DIR / "data" / "market")

    # --- Users ---
    users_data_path: str = str(BASE_DIR / "data" / "users")

    # --- News (sentiment) ---
    news_data_path: str = str(BASE_DIR / "data" / "news")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_mock_llm(self) -> bool:
        return self.llm_mode.lower() != "real"


@lru_cache
def get_settings() -> Settings:
    return Settings()