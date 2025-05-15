from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, PostgresDsn, AnyHttpUrl, SecretStr

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # ── Environment & Logging ────────────────────────────────────────
    ENV: str = Field("local", description="Deployment environment")
    LOG_LEVEL: str = Field("INFO", description="Logging level")

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5433/ingestdb",
        description="Async DB URL"
    )

    # ── Scheduler & Pagination ───────────────────────────────────────
    POLL_INTERVAL_SEC: int = Field(60, description="Pull interval (seconds)")
    PAGE_SIZE: int = Field(30, description="Records per page")

    # ── Source-specific Configs ──────────────────────────────────────
    PLAYSTORE_APP_ID: str = Field(
        ..., env="PLAYSTORE_APP_ID",
        description="Google Play Store package name (e.g. com.example.app)"
    )
    PLAYSTORE_API_KEY: Optional[str] = Field(
        None, env="PLAYSTORE_API_KEY",
        description="OAuth2 Bearer token for Play Store API"
    )
    DISCOURSE_BASE_URL: AnyHttpUrl = Field(
        "https://discourse.example.com",
        description="Base URL for Discourse API"
    )


    # ── Secrets ──────────────────────────────────────────────────────
    INTERCOM_SECRET: Optional[SecretStr] = Field(None, description="HMAC key")
    TWITTER_BEARER_TOKEN: Optional[SecretStr] = Field(None, description="Auth token")

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
