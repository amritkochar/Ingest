import logging

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from core.models import Feedback
from db.models import FeedbackORM
from db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def ingest(feedback: Feedback) -> bool:
    """
    Upsert a single Feedback into the DB. Returns True if inserted, False if duplicate.
    """
    try:
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            stmt = (
                pg_insert(FeedbackORM)
                .values(
                    id=feedback.id,
                    external_id=feedback.external_id,
                    source_type=feedback.source_type,
                    source_instance=feedback.source_instance,
                    tenant_id=feedback.tenant_id,
                    created_at=feedback.created_at,
                    fetched_at=feedback.fetched_at,
                    lang=feedback.lang,
                    body=feedback.body,
                    metadata_=feedback.metadata_,
                )
                .on_conflict_do_nothing(
                    index_elements=[
                        "tenant_id",
                        "source_type",
                        "external_id",
                        "source_instance",
                    ]
                )
            )
            result = await session.execute(stmt)
            await session.commit()

            inserted = result.rowcount == 1
            if not inserted:
                logger.debug(f"Duplicate feedback skipped: {feedback.external_id}")
            else:
                logger.info(f"Inserted feedback: {feedback.external_id}")
            return inserted
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        await session.rollback()
        return False
    except Exception as e:
        logger.error(f"Error ingesting feedback: {e}")
        await session.rollback()
        return False
