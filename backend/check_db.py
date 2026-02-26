import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from src.db.session import engine
from sqlalchemy import inspect

async def check():
    try:
        async with engine.connect() as conn:
            columns = await conn.run_sync(lambda c: inspect(c).get_columns('schedule_polls'))
            print([col['name'] for col in columns])
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
