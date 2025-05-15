# src/workers/scheduler.py
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.time_utils import utc_now
from adapters.discourse import DiscoursePullAdapter
from adapters.intercom import IntercomPullAdapter
from adapters.playstore import PlaystorePullAdapter
from adapters.twitter import TwitterPullAdapter
from config.settings import settings
from services.ingest import ingest


async def dispatch_all() -> None:
    """
    For each configured instance of each platform, pull new records and ingest them.
    Only tenants present in PLATFORM_CONFIG for that platform are iterated.
    """
    now = utc_now()

    # ── Play Store ────────────────────────────────────────────────
    ps_cfg = settings.PLATFORM_CONFIG.get("playstore", {})
    ps_interval = settings.POLL_INTERVALS["playstore"]
    ps_since = now - timedelta(seconds=ps_interval)
    for tenant, apps in ps_cfg.get("apps", {}).items():
        for app_id in apps:
            playstore_adapter = PlaystorePullAdapter(tenant, app_id)
            async for fb in playstore_adapter.fetch(ps_since, now):
                await ingest(fb)

    # ── Twitter ──────────────────────────────────────────────────
    tw_cfg = settings.PLATFORM_CONFIG.get("twitter", {})
    tw_interval = settings.POLL_INTERVALS["twitter"]
    tw_since = now - timedelta(seconds=tw_interval)
    for tenant in tw_cfg.get("queries", {}).keys():
        twitter_adapter = TwitterPullAdapter(tenant)
        async for fb in twitter_adapter.fetch(tw_since, now):
            await ingest(fb)

    # ── Discourse ────────────────────────────────────────────────
    dc_cfg = settings.PLATFORM_CONFIG.get("discourse", {})
    dc_interval = settings.POLL_INTERVALS["discourse"]
    dc_since = now - timedelta(seconds=dc_interval)
    for tenant in dc_cfg.get("base_urls", {}).keys():
        discourse_adapter = DiscoursePullAdapter(tenant)
        async for fb in discourse_adapter.fetch(dc_since, now):
            await ingest(fb)

    # ── Intercom ─────────────────────────────────────────────────
    ic_cfg = settings.PLATFORM_CONFIG.get("intercom", {})
    ic_interval = settings.POLL_INTERVALS["intercom"]
    ic_since = now - timedelta(seconds=ic_interval)
    for tenant in ic_cfg.get("secrets", {}).keys():
        intercom_adapter = IntercomPullAdapter(tenant)
        async for fb in intercom_adapter.fetch(ic_since, now):
            await ingest(fb)


def schedule_jobs() -> None:
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
