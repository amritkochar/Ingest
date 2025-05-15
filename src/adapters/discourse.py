import logging
import uuid
from datetime import datetime
from typing import AsyncIterator

import httpx

from config.settings import settings
from core.models import Feedback
from ports.fetcher import BaseFetcher

logger = logging.getLogger(__name__)

class DiscoursePullAdapter(BaseFetcher):
    """
    Pull “feedback” topics from a Discourse forum via its search API.
    """

    def __init__(self):
        self.base_url = settings.DISCOURSE_BASE_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10)

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = f"{self.base_url}/search.json"
        params = {"q": "feedback"}  # static search term for now

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
        except Exception as e:
            # catch HTTPStatusError, ConnectError, timeouts, etc.
            logger.warning(
                f"Discourse fetch error ({type(e).__name__}): {e}; emitting stub topic"
            )
            yield Feedback(
                id=uuid.uuid4(),
                external_id="stub-discourse",
                source_type="discourse",
                source_instance=self.base_url,
                tenant_id="default",
                created_at=datetime.utcnow(),
                fetched_at=datetime.utcnow(),
                body="This is a stub topic (fetch failure fallback)",
                metadata_={},
            )
            return

        data = resp.json()
        for topic in data.get("topics", []):
            ext_id = str(topic.get("id"))
            # created_at comes back as a Unix timestamp
            created_ts = topic.get("created_at", since.timestamp())
            created_at = datetime.fromtimestamp(created_ts)
            fb = Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="discourse",
                source_instance=self.base_url,
                tenant_id="default",
                created_at=created_at,
                fetched_at=datetime.utcnow(),
                body=topic.get("title"),
                metadata_={"posts_count": topic.get("posts_count")},
            )
            yield fb

        await self.client.aclose()
