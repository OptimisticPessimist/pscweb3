"""Run migration to add schedule_date to attendance_events table."""

import asyncio

from sqlalchemy import text

from src.db import async_session_maker


async def run_migration():
    """Execute migration to add schedule_date column."""
    async with async_session_maker() as session:
        try:
            # Add schedule_date column
            await session.execute(text(
                """
                ALTER TABLE attendance_events 
                ADD COLUMN IF NOT EXISTS schedule_date TIMESTAMP;
                """
            ))
            await session.commit()
            print("✓ Successfully added schedule_date column to attendance_events table")
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())
