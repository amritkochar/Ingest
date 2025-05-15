# src/workers/scheduler.py
import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from adapters.playstore import PlaystorePullAdapter
from adapters.twitter import TwitterPullAdapter
from adapters.discourse import DiscoursePullAdapter
from adapters.intercom import IntercomPullAdapter
from services.ingest import ingest

async def _run_tenant_pulls(tenant_id: str):
    now = datetime.utcnow()

    # Playstore
    ps_since = now - timedelta(seconds=settings.PLAYSTORE_POLL_INTERVAL_SEC)
    ps_adapter = PlaystorePullAdapter(tenant_id)
    async for fb in ps_adapter.fetch(ps_since, now):
        await ingest(fb)

    # Twitter
    tw_since = now - timedelta(seconds=settings.TWITTER_POLL_INTERVAL_SEC)
    tw_adapter = TwitterPullAdapter(tenant_id)
    async for fb in tw_adapter.fetch(tw_since, now):
        await ingest(fb)

    # Discourse
    dc_since = now - timedelta(seconds=settings.DISCOURSE_POLL_INTERVAL_SEC)
    dc_adapter = DiscoursePullAdapter(tenant_id)
    async for fb in dc_adapter.fetch(dc_since, now):
        await ingest(fb)

    # Intercom
    ic_since = now - timedelta(seconds=settings.INTERCOM_POLL_INTERVAL_SEC)
    ic_adapter = IntercomPullAdapter(tenant_id)
    async for fb in ic_adapter.fetch(ic_since, now):
        await ingest(fb)

def schedule_jobs():
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)

    # one job per tenant, all sources together
    for tenant in settings.TENANTS:
        scheduler.add_job(
            _run_tenant_pulls,
            trigger=IntervalTrigger(seconds=settings.DISPATCH_INTERVAL_SEC),
            args=[tenant],
            id=f"pull_all_{tenant}"
        )

    scheduler.start()
