import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def main():
    if not DATABASE_URL:
        print("No DATABASE_URL found.")
        return

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"prepared_statement_cache_size": 0, "statement_cache_size": 0},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("--- Audit Log Stats (Last 24 Hours) ---")
        stmt = text("""
            SELECT event, count(*) 
            FROM audit_logs 
            WHERE created_at > NOW() - INTERVAL '24 hours' 
            GROUP BY event 
            ORDER BY count(*) DESC
        """)
        result = await session.execute(stmt)
        for row in result:
            print(f"{row.event}: {row.count}")


if __name__ == "__main__":
    asyncio.run(main())
