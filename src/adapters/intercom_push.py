import logging
import uuid
from datetime import datetime
from typing import Dict

from config.settings import settings
from core.exceptions import AdapterError
from core.models import Feedback
from ports.push_handler import BasePushHandler

logger = logging.getLogger(__name__)


class IntercomPushHandler(BasePushHandler):
    """
    Handle incoming Intercom webhook JSON for a specific tenant.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        platform_cfg = settings.PLATFORM_CONFIG.get("intercom", {})
        secrets = platform_cfg.get("secrets", {})
        secret_entry = secrets.get(tenant_id)
        if not secret_entry:
            raise AdapterError(f"INTERCOM secret for tenant '{tenant_id}' is not set")
        self.secret = secret_entry.get_secret_value()
        self.signature_header = "X-Intercom-Signature"

    async def handle(self, payload: Dict) -> Feedback:
        # TODO: validate HMAC signature using self.secret if needed
        conv = payload.get("data", {}).get("item", {})
        ext_id = conv.get("id") or str(uuid.uuid4())
        created_ts = conv.get("created_at", datetime.utcnow().timestamp())
        created = datetime.fromtimestamp(created_ts)
        body = conv.get("conversation_message", {}).get("body", "")

        fb = Feedback(
            id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
            external_id=ext_id,
            source_type="intercom",
            source_instance="push",
            tenant_id=self.tenant_id,
            created_at=created,
            fetched_at=datetime.utcnow(),
            lang=conv.get("language"),
            body=body,
            metadata_={"raw": payload},
        )
        logger.info(
            f"Intercom webhook for tenant '{self.tenant_id}' → Feedback {ext_id}"
        )
        return fb
