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


class IntercomPullAdapter(BaseFetcher):
    """Fetch conversations from Intercom via their API."""

    BASE_URL = "https://api.intercom.io"

    def __init__(self):
        token = (
            settings.INTERCOM_SECRET.get_secret_value()
            if settings.INTERCOM_SECRET
            else ""
        )
        if not token:
            raise AdapterError("INTERCOM_SECRET is not set")
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=10)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        self.page_size = settings.PAGE_SIZE

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = "/conversations"
        params = {
            "updated_since": int(since.timestamp()),
            "per_page": self.page_size,
        }

        try:
            resp = await self.client.get(url, params=params, headers=self.headers)
            resp.raise_for_status()
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Intercom 404 – emitting stub conversation")
                yield Feedback(
                    id=uuid.uuid4(),
                    external_id="stub-intercom",
                    source_type="intercom",
                    source_instance="default",
                    tenant_id="default",
                    created_at=datetime.utcnow(),
                    fetched_at=datetime.utcnow(),
                    lang=None,
                    body="This is a stub conversation (404 fallback)",
                    metadata_={},
                )
                return
            raise AdapterError(f"Intercom fetch failed: {e}") from e

        data = resp.json()
        for item in data.get("conversations", []):
            ext_id = item.get("id")
            created_at = datetime.fromtimestamp(
                item.get("created_at", since.timestamp())
            )
            body = item.get("conversation_message", {}).get("body")
            fb = Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="intercom",
                source_instance="default",
                tenant_id="default",
                created_at=created_at,
                fetched_at=datetime.utcnow(),
                lang=item.get("language"),
                body=body,
                metadata_={
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "created_at", "conversation_message")
                },
            )
            yield fb

        await self.client.aclose()
