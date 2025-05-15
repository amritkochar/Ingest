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
    Handle incoming Intercom webhook JSON.
    Expects a payload matching Intercom’s conversation.created or conversation.admin.replied schema.
    """

    def __init__(self):
        secret = (
            settings.INTERCOM_SECRET.get_secret_value()
            if settings.INTERCOM_SECRET
            else ""
        )
        if not secret:
            raise AdapterError("INTERCOM_SECRET is not set")
        self.signature_header = "X-Intercom-Signature"

    async def handle(self, payload: Dict) -> Feedback:
        # TODO: validate HMAC signature from headers if needed
        conv = payload.get("data", {}).get("item", {})
        ext_id = conv.get("id") or str(uuid.uuid4())
        created = datetime.fromtimestamp(
            conv.get("created_at", datetime.utcnow().timestamp())
        )
        body = conv.get("conversation_message", {}).get("body", "")

        fb = Feedback(
            id=uuid.uuid5(uuid.NAMESPACE_URL, ext_id),
            external_id=ext_id,
            source_type="intercom",
            source_instance="push",
            tenant_id=payload.get("tenant_id", "default"),
            created_at=created,
            fetched_at=datetime.utcnow(),
            lang=conv.get("language"),
            body=body,
            metadata_={"raw": payload},
        )
        logger.info(f"Intercom webhook -> Feedback {ext_id}")
        return fb
