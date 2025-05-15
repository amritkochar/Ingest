# src/adapters/playstore.py
import logging
import uuid
from datetime import datetime
from typing import AsyncIterator

import httpx
from httpx import HTTPStatusError
from utils.time_utils import utc_now
from config.settings import settings
from core.exceptions import AdapterError
from core.models import Feedback
from ports.fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class PlaystorePullAdapter(BaseFetcher):
    """
    Pull user reviews from Google Play Store for a specific tenant and app instance.
    """

    BASE_URL = "https://playstore.googleapis.com/v1/applications"

    def __init__(self, tenant_id: str, app_id: str):
        self.tenant_id = tenant_id
        self.app_id = app_id

        cfg = settings.PLATFORM_CONFIG.get("playstore", {})
        apps_map = cfg.get("apps", {})
        if app_id not in apps_map.get(tenant_id, []):
            raise AdapterError(
                f"App '{app_id}' is not configured for tenant '{tenant_id}'"
            )

        self.api_key = cfg.get("api_keys", {}).get(tenant_id, "")
        self.page_size = settings.PAGE_SIZE
        self.client = httpx.AsyncClient(timeout=10)

    async def fetch(self, since: datetime, until: datetime) -> AsyncIterator[Feedback]:
        url = f"{self.BASE_URL}/{self.app_id}/reviews"
        params = {
            "startTime": since.isoformat(),
            "endTime": until.isoformat(),
            "pageSize": str(self.page_size),
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        try:
            resp = await self.client.get(url, params=params, headers=headers)
            resp.raise_for_status()
        except HTTPStatusError as e:
            code = getattr(e.response, "status_code", None)
            if code in (401, 404):
                logger.warning(
                    f"[{self.tenant_id}:{self.app_id}] Playstore {code} → stub"
                )
                yield Feedback(
                    id=uuid.uuid4(),
                    external_id="stub-1",
                    source_type="playstore",
                    source_instance=self.app_id,
                    tenant_id=self.tenant_id,
                    created_at=utc_now(),
                    fetched_at=utc_now(),
                    lang="en",
                    body="This is a stub review (404/401 fallback)",
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
                created_at = utc_now()

            yield Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="playstore",
                source_instance=self.app_id,
                tenant_id=self.tenant_id,
                created_at=created_at,
                fetched_at=utc_now(),
                lang=item.get("languageCode"),
                body=item.get("comment"),
                metadata_={
                    k: v
                    for k, v in item.items()
                    if k not in ("reviewId", "createTime", "comment")
                },
            )

        await self.client.aclose()
