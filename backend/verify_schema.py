
import asyncio
from sqlalchemy import text
from src.db import get_db

async def verify_schema():
    async for session in get_db():
        print("Checking audit_logs columns...")
        result = await session.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'audit_logs'"
        ))
        columns = result.fetchall()
        print("Columns found:", flush=True)
        for col in columns:
            print(f"- {col[0]}: {col[1]}", flush=True)
        break

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_schema())
