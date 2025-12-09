import asyncio
import os
import sys

# パスを通す
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.base import Base
from src.db import engine
from src.db import models  # モデルをインポートしてmetadataに登録させる

async def reset_database():
    print("Resetting database...")
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset complete.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_database())
