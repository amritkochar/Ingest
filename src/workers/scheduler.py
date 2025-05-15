# src/workers/scheduler.py
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import settings
from services.ingest import ingest
from adapters.playstore import PlaystorePullAdapter
from adapters.twitter import TwitterPullAdapter
from adapters.discourse import DiscoursePullAdapter
from adapters.intercom import IntercomPullAdapter

async def dispatch_all():
    """
    For each tenant, for each configured instance of each platform,
    pull new records and ingest them.
    """
    now = datetime.utcnow()

    # ── Play Store ────────────────────────────────────────────────
    ps_interval = settings.POLL_INTERVALS["playstore"]
    ps_since = now - timedelta(seconds=ps_interval)
    for tenant in settings.TENANTS:
        for app_id in settings.PLATFORM_CONFIG["playstore"]["apps"].get(tenant, []):
            adapter = PlaystorePullAdapter(tenant, app_id)
            async for fb in adapter.fetch(ps_since, now):
                await ingest(fb)

    # ── Twitter ─────────────────────────────────────────────────
    tw_interval = settings.POLL_INTERVALS["twitter"]
    tw_since = now - timedelta(seconds=tw_interval)
    for tenant in settings.TENANTS:
        adapter = TwitterPullAdapter(tenant)
        async for fb in adapter.fetch(tw_since, now):
            await ingest(fb)

    # ── Discourse ───────────────────────────────────────────────
    dc_interval = settings.POLL_INTERVALS["discourse"]
    dc_since = now - timedelta(seconds=dc_interval)
    for tenant in settings.TENANTS:
        adapter = DiscoursePullAdapter(tenant)
        async for fb in adapter.fetch(dc_since, now):
            await ingest(fb)

    # ── Intercom ────────────────────────────────────────────────
    ic_interval = settings.POLL_INTERVALS["intercom"]
    ic_since = now - timedelta(seconds=ic_interval)
    for tenant in settings.TENANTS:
        adapter = IntercomPullAdapter(tenant)
        async for fb in adapter.fetch(ic_since, now):
            await ingest(fb)

def schedule_jobs():
    """
    Schedule a single repeating job that calls dispatch_all()
    every DISPATCH_INTERVAL_SEC seconds.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        dispatch_all,
        trigger="interval",
        seconds=settings.DISPATCH_INTERVAL_SEC,
        id="dispatch_all",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
