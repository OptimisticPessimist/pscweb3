
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from dotenv import load_dotenv

load_dotenv("backend/.env")

from src.db.models import Script

async def check_script_content():
    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, connect_args={"statement_cache_size": 0})
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Check Script with title like '刑法十七文字'
        stmt = select(Script).where(Script.title.like("%刑法十七文字%")).limit(1)
        result = await session.execute(stmt)
        script = result.scalar_one_or_none()

        if script:
            print(f"Script Title: {script.title}")
            print(f"Content Start (first 1000 chars):\n")
            print("-" * 50)
            print(script.content[:1000])
            print("-" * 50)
        else:
            print("Script not found.")

if __name__ == "__main__":
    asyncio.run(check_script_content())
