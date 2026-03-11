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

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch the latest 20 audit logs
        result = await session.execute(
            text(
                "SELECT id, event, user_id, project_id, details, ip_address, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 20"
            )
        )
        logs = result.fetchall()
        for log in logs:
            print(
                f"[{log.created_at}] Event: {log.event}, User: {log.user_id}, Project: {log.project_id}"
            )
            print(f"  Details: {log.details}")
            print(f"  IP: {log.ip_address}")
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
