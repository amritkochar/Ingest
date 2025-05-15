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
    Fetch recent tweets matching a query via Twitter API v2.
    """

    BASE_URL = "https://api.twitter.com"

    def __init__(self):
        token = (
            settings.TWITTER_BEARER_TOKEN.get_secret_value()
            if settings.TWITTER_BEARER_TOKEN
            else ""
        )
        if not token:
            raise AdapterError("TWITTER_BEARER_TOKEN is not set")
        query = settings.TWITTER_SEARCH_QUERY
        if not query:
            raise AdapterError("TWITTER_SEARCH_QUERY is not set")

        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=10)
        self.headers = {"Authorization": f"Bearer {token}"}
        self.query = query
        self.page_size = settings.PAGE_SIZE

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
            # Rate-limit fallback stub
            if e.response.status_code == 429 or e.response.status_code == 401:
                logger.warning("Twitter rate limit hit; emitting stub tweet")
                yield Feedback(
                    id=uuid.uuid4(),
                    external_id="stub-twitter",
                    source_type="twitter",
                    source_instance="search",
                    tenant_id="default",
                    created_at=datetime.utcnow(),
                    fetched_at=datetime.utcnow(),
                    body="Stub tweet due to rate limit",
                    metadata_={},
                )
                return
            raise AdapterError(f"Twitter fetch failed: {e}") from e

        data = resp.json()
        for item in data.get("data", []):
            ext_id = item.get("id")
            text = item.get("text")
            # parse ISO timestamp, stripping trailing Z if present
            ts = item.get("created_at").rstrip("Z")
            created_at = datetime.fromisoformat(ts)
            fb = Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="twitter",
                source_instance="search",
                tenant_id="default",
                created_at=created_at,
                fetched_at=datetime.utcnow(),
                body=text,
                metadata_={
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "text", "created_at")
                },
            )
            yield fb

        await self.client.aclose()
