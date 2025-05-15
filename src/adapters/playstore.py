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


class PlaystorePullAdapter(BaseFetcher):
    def __init__(self):
        self.app_id = settings.PLAYSTORE_APP_ID
        self.api_key = settings.PLAYSTORE_API_KEY or ""
        self.page_size = settings.PAGE_SIZE
        self.client = httpx.AsyncClient(timeout=10)

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = f"https://playstore.googleapis.com/v1/applications/{self.app_id}/reviews"
        params = {
            "startTime": since.isoformat(),
            "endTime": until.isoformat(),
            "pageSize": self.page_size,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        try:
            resp = await self.client.get(url, params=params, headers=headers)
            resp.raise_for_status()
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Play Store API 404 for app {self.app_id}, emitting stub review"
                )
                yield Feedback(
                    id=uuid.uuid4(),
                    external_id="stub-1",
                    source_type="playstore",
                    source_instance=self.app_id,
                    tenant_id="default",
                    created_at=datetime.utcnow(),
                    fetched_at=datetime.utcnow(),
                    lang="en",
                    body="This is a stub review (404 fallback)",
                    metadata_={},
                )
                return
            raise AdapterError(f"Play Store fetch failed: {e}") from e

        data = resp.json()
        for item in data.get("reviews", []):
            ext_id = item.get("reviewId")
            try:
                created_at = datetime.fromisoformat(item.get("createTime"))
            except Exception:
                created_at = datetime.utcnow()
            fb = Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="playstore",
                source_instance=self.app_id,
                tenant_id="default",
                created_at=created_at,
                fetched_at=datetime.utcnow(),
                lang=item.get("languageCode"),
                body=item.get("comment"),
                metadata_={
                    k: v
                    for k, v in item.items()
                    if k not in ("reviewId", "createTime", "comment")
                },
            )
            yield fb

        await self.client.aclose()
