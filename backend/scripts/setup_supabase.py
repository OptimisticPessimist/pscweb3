import asyncio
import os
import sys

# Add parent directory to path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings
from src.db.models import Base


async def init_db():
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        connect_args={"statement_cache_size": 0},
    )
    try:
        async with engine.begin() as conn:
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
