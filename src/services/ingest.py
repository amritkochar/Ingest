import logging
from sqlalchemy import insert, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import AsyncSessionLocal
from db.models import FeedbackORM
from core.models import Feedback
from core.exceptions import DuplicateRecordError

logger = logging.getLogger(__name__)

async def ingest(feedback: Feedback) -> bool:
    """
    Upsert a single Feedback into the DB. Returns True if inserted, False if duplicate.
    """
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        stmt = pg_insert(FeedbackORM).values(
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
        ).on_conflict_do_nothing(
            index_elements=[
                "tenant_id",
                "source_type",
                "external_id",
                "source_instance",
            ]
        )
        result = await session.execute(stmt)
        await session.commit()

        inserted = result.rowcount == 1
        if not inserted:
            logger.debug(f"Duplicate feedback skipped: {feedback.external_id}")
        else:
            logger.info(f"Inserted feedback: {feedback.external_id}")
        return inserted
