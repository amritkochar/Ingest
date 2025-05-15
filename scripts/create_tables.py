#!/usr/bin/env python
import asyncio
from db.models import Base
from db.session import engine

async def main():
    async with engine.begin() as conn:
        # Drop & recreate all tables (safe in dev)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ Tables created")

if __name__ == "__main__":
    asyncio.run(main())
