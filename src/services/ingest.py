# src/services/ingest.py
import logging

from sqlalchemy.exc import IntegrityError

from core.models import Feedback
from db.models import FeedbackORM
from db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def ingest(feedback: Feedback) -> bool:
    """
    Insert a Feedback record. Returns True if inserted, False if a duplicate or on error.
    This version simply ADDs the ORM object and relies on the DB's unique constraint
    (tenant_id, source_type, external_id, source_instance) turning duplicates into
    IntegrityError, which we catch and treat as "not inserted".
    """
    async with AsyncSessionLocal() as session:
        try:
            # build ORM instance directly
            obj = FeedbackORM(**feedback.dict())
            session.add(obj)
            await session.commit()
            logger.info(f"Inserted feedback: {feedback.external_id}")
            return True
        except IntegrityError:
            await session.rollback()
            logger.info(f"Duplicate feedback skipped: {feedback.external_id}")
            return False
        except Exception as e:
            await session.rollback()
            logger.error(f"Error ingesting feedback {feedback.external_id}: {e}")
            return False
