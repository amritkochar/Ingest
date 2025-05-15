# src/adapters/discourse.py
import logging
import uuid
from datetime import datetime
from typing import AsyncIterator

import httpx
from utils.time_utils import utc_now
from config.settings import settings
from core.models import Feedback
from ports.fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class DiscoursePullAdapter(BaseFetcher):
    """
    Pull “feedback” topics from a Discourse forum via its search API,
    for a specific tenant.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        cfg = settings.PLATFORM_CONFIG.get("discourse", {})
        base_urls = cfg.get("base_urls", {})
        base = base_urls.get(tenant_id)
        if not base:
            raise ValueError(f"No Discourse URL configured for tenant '{tenant_id}'")
        self.base_url = base.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10)

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = f"{self.base_url}/search.json"
        params = {"q": "feedback"}  # static for now

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(
                f"Discourse fetch error ({type(e).__name__}): {e}; "
                f"emitting stub topic for tenant '{self.tenant_id}'"
            )
            yield Feedback(
                id=uuid.uuid4(),
                external_id="stub-discourse",
                source_type="discourse",
                source_instance=self.base_url,
                tenant_id=self.tenant_id,
                created_at=utc_now(),
                fetched_at=utc_now(),
                lang = None,
                body="This is a stub topic (fetch failure fallback)",
                metadata_={},
            )
            return

        data = resp.json()
        for topic in data.get("topics", []):
            ext_id = str(topic.get("id"))
            created_ts = topic.get("created_at", since.timestamp())
            created_at = datetime.fromtimestamp(created_ts)
            yield Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="discourse",
                source_instance=self.base_url,
                tenant_id=self.tenant_id,
                created_at=created_at,
                fetched_at=utc_now(),
                lang = None,
                body=topic.get("title"),
                metadata_={"posts_count": topic.get("posts_count")},
            )

        await self.client.aclose()
