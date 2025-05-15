# tests/services/test_ingest.py
import pytest
import uuid
from datetime import datetime

from core.models import Feedback
from services.ingest import ingest
from db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@pytest.fixture
async def sqlite_session():
    url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    yield session_factory
    await engine.dispose()

@pytest.mark.asyncio
async def test_ingest_insert_and_duplicate(monkeypatch, sqlite_session):
    # override AsyncSessionLocal
    monkeypatch.setattr("services.ingest.AsyncSessionLocal", sqlite_session)
    
    fb = Feedback(
        id=uuid.uuid4(), external_id="e1", source_type="playstore",
        source_instance="app1", tenant_id="t1",
        created_at=datetime.utcnow(), fetched_at=datetime.utcnow(),
        lang="en", body="hi", metadata_={}
    )

    # first insert
    inserted1 = await ingest(fb)
    assert inserted1 is True

    # duplicate
    inserted2 = await ingest(fb)
    assert inserted2 is False