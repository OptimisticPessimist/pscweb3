import asyncio
import os
import sys

# Add parent directory to path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine
from src.db.models import Base
from src.config import settings

# Explicit connection string from user (with async driver)
# Note: SQLAlchemy async requires postgresql+asyncpg://
# The user provided: postgresql://...
# We need to switch the scheme.
RAW_URL = "postgresql://postgres.azggoytepdajynlhecxo:RCxufVTBEHS7h6%@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
DB_URL = RAW_URL.replace("postgresql://", "postgresql+asyncpg://")

async def init_db():
    print(f"Connecting to: {DB_URL}")
    try:
        engine = create_async_engine(DB_URL, echo=True)
        async with engine.begin() as conn:
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
