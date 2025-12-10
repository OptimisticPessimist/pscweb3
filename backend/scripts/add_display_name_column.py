import asyncio
import os

# DB URL (Assuming default from .env or explicit)
# For this project, it seems to use env var DATABASE_URL.
# Creating engine directly from env var or hardcoded if needed for this script context.
# I'll rely on os.environ being set or use the common dev url.
# In previous logs, user has PostgreSQL (Neon).
# I'll try to import settings.
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import settings


async def add_column():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE project_members ADD COLUMN display_name VARCHAR(100);"))
            print("Successfully added display_name column.")
        except Exception as e:
            print(f"Error (maybe column exists?): {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_column())
