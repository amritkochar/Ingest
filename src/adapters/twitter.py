# src/adapters/twitter.py
import logging
import uuid
from datetime import datetime
from typing import AsyncIterator

import httpx
from httpx import HTTPStatusError

from config.settings import settings
from core.exceptions import AdapterError
from core.models import Feedback
from ports.fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class TwitterPullAdapter(BaseFetcher):
    """
    Fetch recent tweets matching a query via Twitter API v2 for a specific tenant.
    """

    BASE_URL = "https://api.twitter.com"

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        cfg = settings.PLATFORM_CONFIG.get("twitter", {})
        tokens = cfg.get("tokens", {})
        queries = cfg.get("queries", {})

        token_entry = tokens.get(tenant_id)
        query = queries.get(tenant_id)
        if not token_entry:
            raise AdapterError(
                f"TWITTER_BEARER_TOKEN for tenant '{tenant_id}' is not set"
            )
        if not query:
            raise AdapterError(
                f"TWITTER_SEARCH_QUERY for tenant '{tenant_id}' is not set"
            )

        self.token = token_entry.get_secret_value()
        self.query = query
        self.page_size = settings.PAGE_SIZE

        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=10)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = "/2/tweets/search/recent"
        params = {
            "query": self.query,
            "start_time": since.isoformat() + "Z",
            "end_time": until.isoformat() + "Z",
            "max_results": self.page_size,
        }

        try:
            resp = await self.client.get(url, params=params, headers=self.headers)
            resp.raise_for_status()
        except HTTPStatusError as e:
            code = getattr(e.response, "status_code", None)
            if code in (401, 429):
                logger.warning(
                    f"[{self.tenant_id}] Twitter fetch error {code}; emitting stub tweet"
                )
                yield Feedback(
                    id=uuid.uuid4(),
                    external_id="stub-twitter",
                    source_type="twitter",
                    source_instance="search",
                    tenant_id=self.tenant_id,
                    created_at=datetime.utcnow(),
                    fetched_at=datetime.utcnow(),
                    lang = None,
                    body="Stub tweet due to rate limit or auth error",
                    metadata_={},
                )
                return
            raise AdapterError(f"Twitter fetch failed: {e}") from e

        data = resp.json()
        for item in data.get("data", []):
            ext_id = item.get("id")
            text = item.get("text")
            ts = item.get("created_at", "").rstrip("Z")
            try:
                created_at = datetime.fromisoformat(ts)
            except Exception:
                created_at = datetime.utcnow()

            yield Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="twitter",
                source_instance="search",
                tenant_id=self.tenant_id,
                created_at=created_at,
                fetched_at=datetime.utcnow(),
                lang = None,
                body=text,
                metadata_={
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "text", "created_at")
                },
            )

        await self.client.aclose()
