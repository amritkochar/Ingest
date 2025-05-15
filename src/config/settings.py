from pathlib import Path
from typing import Optional, List, Dict

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
    
    # ── Multi‐tenant stub support ──────────────────────────────────
    TENANTS: List[str] = Field(
        default_factory=lambda: ["tenant1", "tenant2", "tenant3", "tenant4", "tenant5"],
        description="List of tenant IDs; stubs will pick one at random"
    )
    
    # ── Per‐tenant configs ───────────────────────────────────────────
    PLAYSTORE_APPS: Dict[str, str] = Field(
        default_factory=lambda: {
            "tenant1": "com.example.app1",
            "tenant2": "com.example.app2",
            "tenant3": "com.other.app",
            # etc…
        },
        description="Map of tenant_id → Google Play app ID"
    )

    TWITTER_QUERIES: Dict[str, str] = Field(
        default_factory=lambda: {
            "tenant1": "#feedback1 lang:en",
            "tenant2": "#feedback2 lang:en",
            # …
        },
        description="Map of tenant_id → recent‐search query"
    )
    TWITTER_BEARER_TOKENS: Dict[str, SecretStr] = Field(
        default_factory=lambda: {
            "tenant1": SecretStr("token1"),
            "tenant2": SecretStr("token2"),
            # …
        },
        description="Map of tenant_id → Twitter bearer token"
    )

    DISCOURSE_BASE_URLS: Dict[str, AnyHttpUrl] = Field(
        default_factory=lambda: {
            "tenant1": "https://discourse1.example.com",
            "tenant2": "https://discourse2.example.com",
        },
        description="Map of tenant_id → Discourse base URLs"
    )

    INTERCOM_SECRETS: Dict[str, SecretStr] = Field(
        default_factory=lambda: {
            "tenant1": SecretStr("secret1"),
            "tenant2": SecretStr("secret2"),
        },
        description="Map of tenant_id → Intercom webhook shared secret"
    )

    # ── Scheduler & Pagination ───────────────────────────────────────
    # ── Poll intervals (in seconds) ───────────────────────────────────
    PLAYSTORE_POLL_INTERVAL_SEC: int = Field(
        60, description="Poll Play Store every N seconds"
    )
    TWITTER_POLL_INTERVAL_SEC: int = Field(
        60, description="Poll Twitter every N seconds"
    )
    DISCOURSE_POLL_INTERVAL_SEC: int = Field(
        60, description="Poll Discourse every N seconds"
    )
    INTERCOM_POLL_INTERVAL_SEC: int = Field(
        60, description="Poll Intercom every N seconds"
    )
    
    DISPATCH_INTERVAL_SEC: int = Field(
        60,
        description="Seconds between each multi‐tenant dispatch run"
    )

    PAGE_SIZE: int = Field(30, description="Records per page")

    # ── Source-specific Configs ──────────────────────────────────────
    PLAYSTORE_APP_ID: str = Field(
        ...,
        env="PLAYSTORE_APP_ID",
        description="Google Play Store package name (e.g. com.example.app)",
    )
    PLAYSTORE_API_KEY: Optional[str] = Field(
        None,
        env="PLAYSTORE_API_KEY",
        description="OAuth2 Bearer token for Play Store API",
    )
    DISCOURSE_BASE_URL: AnyHttpUrl = Field(
        "https://discourse.example.com", description="Base URL for Discourse API"
    )
    TWITTER_SEARCH_QUERY: str = Field(
        "",
        env="TWITTER_SEARCH_QUERY",
        description="Twitter Recent Search query (e.g. '#feedback lang:en')",
    )
    TWITTER_BEARER_TOKEN: Optional[SecretStr] = Field(
        None, env="TWITTER_BEARER_TOKEN", description="Bearer token for Twitter API"
    )
    INTERCOM_SECRET: Optional[SecretStr] = Field(None, description="HMAC key")

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
