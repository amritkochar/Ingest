import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Request

from adapters.intercom_push import IntercomPushHandler
from config.settings import settings
from core.models import Feedback
from db.models import FeedbackORM
from db.session import AsyncSessionLocal
from ports.push_handler import BasePushHandler
from services.ingest import ingest
from workers.scheduler import schedule_jobs

logging.basicConfig(
    level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    schedule_jobs()
    yield
    # shutdown logic (if any)
    # e.g. await some_cleanup()


app = FastAPI(lifespan=lifespan)


# ── Health Check ────────────────────────────────────────
@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


# ── Webhook endpoint (Intercom push) ────────────────────────────────
@app.post("/webhook/intercom/{tenant_id}")
async def intercom_webhook(tenant_id: str, request: Request) -> dict:
    payload = await request.json()
    payload["tenant_id"] = tenant_id

    handler: BasePushHandler = IntercomPushHandler(tenant_id)
    try:
        fb = await handler.handle(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    inserted = await ingest(fb)
    return {"status": "ok", "inserted": inserted}


# ── Search feedback within a time range ──────────────────────────────
@app.get("/feedback", response_model=List[Feedback])
async def search_feedback(
    tenant_id: str = Query(...),
    source_type: Optional[str] = Query(None),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    metadata_key: Optional[str] = Query(None),
    metadata_val: Optional[str] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
) -> List[Feedback]:
    filters = [FeedbackORM.tenant_id == tenant_id]
    if source_type:
        filters.append(FeedbackORM.source_type == source_type)
    if start is not None:
        filters.append(FeedbackORM.created_at >= start)
    if end is not None:
        filters.append(FeedbackORM.created_at <= end)
    if metadata_key and metadata_val:
        filters.append(FeedbackORM.metadata_[metadata_key].astext == metadata_val)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            FeedbackORM.__table__.select().where(*filters).limit(limit)
        )
        rows = result.fetchall()
        return [Feedback.from_orm(r) for r in rows]


# ── Fetch a specific feedback by its UUID ───────────────────────────
@app.get("/feedback/{feedback_id}", response_model=Feedback)
async def get_feedback(feedback_id: UUID, tenant_id: str = Query(...)) -> Feedback:
    async with AsyncSessionLocal() as session:
        fb_orm = await session.get(FeedbackORM, feedback_id)
    if not fb_orm or fb_orm.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Not found")
    return Feedback.from_orm(fb_orm)
