# src/db/models.py

from sqlalchemy import Column, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FeedbackORM(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_type",
            "external_id",
            "source_instance",
            name="uq_feedback_tenant_source_external",
        ),
        # GIN index on metadata_ JSONB
        Index("idx_feedback_metadata", "metadata_", postgresql_using="gin"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    external_id = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_instance = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    lang = Column(String, nullable=True)
    body = Column(String, nullable=True)
    metadata_ = Column(JSONB, nullable=False, default={})
