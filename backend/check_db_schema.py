
import asyncio

from sqlalchemy import text

from src.db import async_session_factory


async def check_schema():
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'scripts'"))
        columns = result.fetchall()
        print("Columns in scripts table:")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")

if __name__ == "__main__":
    asyncio.run(check_schema())
