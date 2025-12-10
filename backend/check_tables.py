
import asyncio

from sqlalchemy import text

from src.db import get_db


async def list_tables():
    async for session in get_db():
        print("Checking tables...")
        # Postgres query to list tables
        result = await session.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        tables = result.scalars().all()
        print("Tables found:")
        for t in tables:
            print(f"- {t}")

        if "audit_logs" in tables:
            print("CONFIRMED: audit_logs table exists.")
        else:
            print("MISSING: audit_logs table NOT found.")
        break

if __name__ == "__main__":
    import sys
    # Fix for windows selector event loop if needed, but uv run handles env usually
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(list_tables())
