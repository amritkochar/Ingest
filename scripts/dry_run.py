#!/usr/bin/env python

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from config.settings import settings
from core.models import Feedback
from services.ingest import ingest
from utils.time_utils import utc_now

async def main() -> None:
    now = utc_now()
    platforms = list(settings.PLATFORM_CONFIG.keys())

    for i in range(200):
        # pick a random tenant + platform
        tenant = random.choice(settings.TENANTS)
        plat = random.choice(platforms)
        cfg = settings.PLATFORM_CONFIG.get(plat, {})

        # determine a valid "instance" for that tenant+platform
        if plat == "playstore":
            apps = cfg.get("apps", {}).get(tenant, [])
            if not apps:
                continue
            instance = random.choice(apps)
        elif plat == "twitter":
            instance = "search"
        elif plat == "discourse":
            # use the base_url as the instance key
            instance = cfg.get("base_urls", {}).get(tenant)
            if not instance:
                continue
        elif plat == "intercom":
            instance = "push"
        else:
            continue

        # random timestamp in last 30 days
        created_at = now - timedelta(days=random.random() * 30)
        fetched_at = created_at + timedelta(seconds=random.randint(1, 300))

        fb = Feedback(
            id=uuid.uuid4(),
            external_id=f"{plat}-{tenant}-{i}",
            source_type=plat,
            source_instance=str(instance),
            tenant_id=tenant,
            created_at=created_at,
            fetched_at=fetched_at,
            lang="en",
            body=f"Dry-run message #{i} on {plat}",
            metadata_={"dry_run": True, "index": i},
        )

        inserted = await ingest(fb)
        print(f"{'→' if inserted else '✗'} {fb.external_id}")


if __name__ == "__main__":
    asyncio.run(main())
