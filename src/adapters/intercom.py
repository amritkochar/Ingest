# src/adapters/intercom.py
import logging
import uuid
from datetime import datetime
from typing import AsyncIterator

import httpx

from config.settings import settings
from core.exceptions import AdapterError
from core.models import Feedback
from ports.fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class IntercomPullAdapter(BaseFetcher):
    """Fetch conversations from Intercom via their API for a specific tenant."""

    BASE_URL = "https://api.intercom.io"

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        cfg = settings.PLATFORM_CONFIG.get("intercom", {})
        secrets = cfg.get("secrets", {})
        secret_entry = secrets.get(tenant_id)
        if not secret_entry:
            raise AdapterError(f"INTERCOM secret for tenant '{tenant_id}' is not set")
        token = secret_entry.get_secret_value()
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
        except Exception as e:
            logger.warning(
                f"Intercom fetch error ({type(e).__name__}): {e}; "
                f"emitting stub conversation for tenant '{self.tenant_id}'"
            )
            yield Feedback(
                id=uuid.uuid4(),
                external_id="stub-intercom",
                source_type="intercom",
                source_instance="pull",
                tenant_id=self.tenant_id,
                created_at=datetime.utcnow(),
                fetched_at=datetime.utcnow(),
                lang=None,
                body="This is a stub conversation (fetch failure fallback)",
                metadata_={},
            )
            return

        data = resp.json()
        for item in data.get("conversations", []):
            ext_id = item.get("id")
            created_at = datetime.fromtimestamp(
                item.get("created_at", since.timestamp())
            )
            body = item.get("conversation_message", {}).get("body", "")
            meta = {
                k: v
                for k, v in item.items()
                if k not in ("id", "created_at", "conversation_message")
            }
            yield Feedback(
                id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
                external_id=ext_id,
                source_type="intercom",
                source_instance="pull",
                tenant_id=self.tenant_id,
                created_at=created_at,
                fetched_at=datetime.utcnow(),
                lang=item.get("language"),
                body=body,
                metadata_=meta,
            )

        await self.client.aclose()
