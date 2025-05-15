# src/config/settings.py

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import AnyHttpUrl, BaseSettings, Field, PostgresDsn, SecretStr

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── Environment & Logging ────────────────────────────────────────
    ENV: str = Field("local", description="Deployment environment")
    LOG_LEVEL: str = Field("INFO", description="Logging level")

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        "postgresql+asyncpg://postgres:postgres@db:5432/ingestdb",
        description="Async DB URL",
    )

    # ── Tenants ───────────────────────────────────────────────────────
    TENANTS: List[str] = Field(
        default_factory=lambda: ["tenant1", "tenant2", "tenant3", "tenant4", "tenant5"],
        description="List of tenant IDs"
    )

    # ── Multi-tenant, multi-instance service configs ─────────────────
    PLATFORM_CONFIG: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "playstore": {
                "apps": {
                    "tenant1": ["com.example.app1", "com.example.app2"],
                    "tenant2": ["com.other.app"],
                    # …
                },
                "api_keys": {
                    "tenant1": "playstore_key1",
                    "tenant2": "playstore_key2",
                    # …
                },
            },
            "twitter": {
                "queries": {
                    "tenant1": "#feedback1 lang:en",
                    "tenant2": "#feedback2 lang:en",
                    # …
                },
                "tokens": {
                    "tenant1": SecretStr("twitter_token1"),
                    "tenant2": SecretStr("twitter_token2"),
                    # …
                },
            },
            "discourse": {
                "base_urls": {
                    "tenant1": "https://discourse1.example.com",
                    "tenant2": "https://discourse2.example.com",
                    # …
                }
            },
            "intercom": {
                "secrets": {
                    "tenant1": SecretStr("intercom_secret1"),
                    "tenant2": SecretStr("intercom_secret2"),
                    # …
                }
            },
        },
        description="Per-platform, per-tenant instance mappings",
    )

    # ── Polling intervals (in seconds) ───────────────────────────────
    POLL_INTERVALS: Dict[str, int] = Field(
        default_factory=lambda: {
            "playstore": 60,
            "twitter": 60,
            "discourse": 60,
            "intercom": 60,
        },
        description="Frequency per platform in seconds",
    )

    DISPATCH_INTERVAL_SEC: int = Field(
        60,
        description="Interval between each full dispatch run",
    )

    PAGE_SIZE: int = Field(
        30,
        description="Default page size for all API calls",
    )

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
