#!/usr/bin/env python
import asyncio
from datetime import datetime, timedelta

from adapters.playstore import PlaystorePullAdapter
from services.ingest import ingest

async def main():
    adapter = PlaystorePullAdapter()
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    async for fb in adapter.fetch(since=since, until=until):
        ok = await ingest(fb)
        print("→ ingested:", fb.external_id, "success=", ok)

if __name__ == "__main__":
    asyncio.run(main())
