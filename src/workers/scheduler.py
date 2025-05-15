import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from adapters.discourse import DiscoursePullAdapter
from adapters.intercom import IntercomPullAdapter
from adapters.playstore import PlaystorePullAdapter
from adapters.twitter import TwitterPullAdapter
from config.settings import settings
from services.ingest import ingest


async def _run_pull(adapter, interval_sec):
    """
    Fetch from `interval_sec` ago until now and ingest.
    """
    now = datetime.utcnow()
    since = now - timedelta(seconds=interval_sec)
    async for fb in adapter.fetch(since=since, until=now):
        await ingest(fb)


def schedule_jobs():
    # 1. Get the running event loop (Uvicorn’s loop)
    loop = (
        asyncio.get_event_loop()
    )  # returns the currently running loop :contentReference[oaicite:5]{index=5}

    # 2. Bind scheduler to that loop
    scheduler = AsyncIOScheduler(
        event_loop=loop
    )  # ensures jobs run in this loop :contentReference[oaicite:6]{index=6}

    # 3. Register each pull as a coroutine job
    scheduler.add_job(
        _run_pull,
        trigger=IntervalTrigger(seconds=settings.PLAYSTORE_POLL_INTERVAL_SEC),
        args=[PlaystorePullAdapter(), settings.PLAYSTORE_POLL_INTERVAL_SEC],
        id="playstore_pull",
    )
    scheduler.add_job(
        _run_pull,
        trigger=IntervalTrigger(seconds=settings.TWITTER_POLL_INTERVAL_SEC),
        args=[TwitterPullAdapter(), settings.TWITTER_POLL_INTERVAL_SEC],
        id="twitter_pull",
    )
    scheduler.add_job(
        _run_pull,
        trigger=IntervalTrigger(seconds=settings.DISCOURSE_POLL_INTERVAL_SEC),
        args=[DiscoursePullAdapter(), settings.DISCOURSE_POLL_INTERVAL_SEC],
        id="discourse_pull",
    )
    scheduler.add_job(
        _run_pull,
        trigger=IntervalTrigger(seconds=settings.INTERCOM_POLL_INTERVAL_SEC),
        args=[IntercomPullAdapter(), settings.INTERCOM_POLL_INTERVAL_SEC],
        id="intercom_pull",
    )

    # 4. Start the scheduler (non‐blocking)
    scheduler.start()  # runs within the provided event loop :contentReference[oaicite:7]{index=7}
