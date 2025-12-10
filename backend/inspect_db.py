import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.db.models import Rehearsal, RehearsalCast, RehearsalParticipant, User

DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def inspect_db():
    sys.stdout.reconfigure(encoding='utf-8')
    async with AsyncSessionLocal() as db:
        print("\n--- Users ---")
        result = await db.execute(select(User))
        users = result.scalars().all()
        real_user = None
        for u in users:
            print(f"ID: {u.id}, Name: {u.discord_username}, DiscordID: {u.discord_id}")
            if u.discord_username != "ScheduleTester":
                real_user = u

        if not real_user:
            print("No real user found (excluding ScheduleTester).")
            return

        print(f"\n--- Checking Schedule for: {real_user.discord_username} ({real_user.id}) ---")

        print("\n--- Rehearsal Participants (User only) ---")
        result = await db.execute(
            select(RehearsalParticipant)
            .where(RehearsalParticipant.user_id == real_user.id)
        )
        parts = result.scalars().all()
        for p in parts:
            print(f" - RehearsalID: {p.rehearsal_id}")

        if not parts:
            print("No participation entries found.")

        print("\n--- Rehearsal Casts (User only) ---")
        result = await db.execute(
            select(RehearsalCast)
            .where(RehearsalCast.user_id == real_user.id)
        )
        casts = result.scalars().all()
        for c in casts:
            print(f" - RehearsalID: {c.rehearsal_id}")

        if not casts:
            print("No cast entries found.")

        # Check actual Rehearsal objects to ensure they exist and have dates
        if parts or casts:
            param_r_ids = [p.rehearsal_id for p in parts] + [c.rehearsal_id for c in casts]
            if param_r_ids:
                print(f"\n--- Rehearsal Details ({len(param_r_ids)} found) ---")
                r_result = await db.execute(select(Rehearsal).where(Rehearsal.id.in_(param_r_ids)))
                rehearsals = r_result.scalars().all()
                for r in rehearsals:
                    print(f" - ID: {r.id}, Date: {r.date}")


if __name__ == "__main__":
    try:
        asyncio.run(inspect_db())
    except Exception:
        import traceback
        traceback.print_exc()
