# tests/services/test_ingest.py

import uuid
from datetime import datetime

import pytest
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.models import Feedback
from db.models import Base, FeedbackORM
from services.ingest import ingest


@pytest.fixture
async def sqlite_session():
    # Use in-memory SQLite
    url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(url, echo=False)

    # Monkey-patch JSONB → SQLite JSON
    FeedbackORM.__table__.c.metadata_.type = SQLiteJSON()

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    yield session_factory

    await engine.dispose()


@pytest.mark.asyncio
async def test_ingest_insert_and_duplicate(monkeypatch, sqlite_session):
    # Override the AsyncSessionLocal used by ingest()
    monkeypatch.setattr("services.ingest.AsyncSessionLocal", sqlite_session)

    fb = Feedback(
        id=uuid.uuid4(),
        external_id="e1",
        source_type="playstore",
        source_instance="app1",
        tenant_id="t1",
        created_at=datetime.utcnow(),
        fetched_at=datetime.utcnow(),
        lang="en",
        body="hi",
        metadata_={},  # now maps to SQLite JSON
    )

    # First insert should return True
    inserted1 = await ingest(fb)
    assert inserted1 is True

    # Second (duplicate) insert should return False
    inserted2 = await ingest(fb)
    assert inserted2 is False
