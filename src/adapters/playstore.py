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
    """
    Pull user reviews from Google Play Store for a specific tenant.
    """

    BASE_URL = "https://playstore.googleapis.com/v1/applications"

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.app_id = settings.PLAYSTORE_APPS.get(tenant_id)
        if not self.app_id:
            raise AdapterError(f"No Playstore app ID for tenant '{tenant_id}'")
        self.api_key = settings.PLAYSTORE_API_KEY or ""
        self.page_size = settings.PAGE_SIZE
        self.client = httpx.AsyncClient(timeout=10)

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = f"{self.BASE_URL}/{self.app_id}/reviews"
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
            code = e.response.status_code if e.response else None
            if code in (401, 404):
                logger.warning(
                    f"Playstore fetch error {code} for app {self.app_id}; emitting stub review for {self.tenant_id}"
                )
                yield Feedback(
                    id=uuid.uuid4(),
                    external_id="stub-1",
                    source_type="playstore",
                    source_instance=self.app_id,
                    tenant_id=self.tenant_id,
                    created_at=datetime.utcnow(),
                    fetched_at=datetime.utcnow(),
                    lang="en",
                    body="This is a stub review (404 fallback)",
                    metadata_={},
                )
                return
            raise AdapterError(f"Playstore fetch failed: {e}") from e

        data = resp.json()
        for item in data.get("reviews", []):
            ext_id = item.get("reviewId")
            try:
                created_at = datetime.fromisoformat(item.get("createTime"))
            except Exception:
                created_at = datetime.utcnow()
            yield Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="playstore",
                source_instance=self.app_id,
                tenant_id=self.tenant_id,
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

        await self.client.aclose()
