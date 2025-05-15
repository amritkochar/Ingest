#!/usr/bin/env python
import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/ingestdb"
)


async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("DB ok:", result.scalar())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
