import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def get_test_invitation():
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
        # Get a relatively recent, valid invitation
        stmt = text("""
            SELECT token, project_id 
            FROM project_invitations 
            WHERE (expires_at IS NULL OR expires_at > NOW()) 
              AND (max_uses IS NULL OR used_count < max_uses)
            LIMIT 1
        """)
        result = await session.execute(stmt)
        row = result.fetchone()
        if row:
            print(f"INVITATION_TOKEN={row.token}")
            print(f"PROJECT_ID={row.project_id}")
        else:
            print("No valid invitation found in DB.")


if __name__ == "__main__":
    asyncio.run(get_test_invitation())
