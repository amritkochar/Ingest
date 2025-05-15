from pathlib import Path
from typing import Optional

from pydantic import PostgresDsn, SecretStr, AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # ── Environment & Logging ───────────────────────────────────────────
    ENV: str = Field("local", description="Deployment environment")
    LOG_LEVEL: str = Field("INFO", description="Logging level")

    # ── Database ────────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/ingestdb",
        description="Async DB URL"
    )

    # ── Scheduler & Pagination ──────────────────────────────────────────
    POLL_INTERVAL_SEC: int = Field(60, description="Pull interval (seconds)")
    PAGE_SIZE: int = Field(30, description="Records per page")

    # ── Source-specific Configs ─────────────────────────────────────────
    PLAYSTORE_API_KEY: Optional[str] = Field(None, description="Play Store API key")
    DISCOURSE_BASE_URL: AnyHttpUrl = Field(
        "https://discourse.example.com",
        description="Base URL for Discourse API"
    )

    # ── Secrets ──────────────────────────────────────────────────────────
    INTERCOM_SECRET: Optional[SecretStr] = Field(None, description="HMAC secret for Intercom")
    TWITTER_BEARER_TOKEN: Optional[SecretStr] = Field(None, description="Twitter auth token")

    # ── Pydantic Settings Configuration ─────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",        # auto-load .env at startup
        env_file_encoding="utf-8",
        env_prefix="INGEST_",              # all vars must start with INGEST_
        env_nested_delimiter="__",         # support nested models via __
        extra="ignore",                    # ignore unexpected env vars
    )

# Singleton instance for import
settings = Settings()
