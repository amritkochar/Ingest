import logging
from core.models import Feedback
from core.exceptions import DuplicateRecordError

logger = logging.getLogger(__name__)

async def ingest(feedback: Feedback) -> bool:
    """
    Stub: accept a Feedback, log it, and return True.
    Later: upsert into DB with idempotency.
    """
    logger.info(f"INGEST stub: {feedback.external_id}")
    return True
