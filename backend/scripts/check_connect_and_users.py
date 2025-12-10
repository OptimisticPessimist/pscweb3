import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, text
from src.db import async_session_maker
from src.db.models import User

async def check_db():
    print("Checking DB connection...")
    try:
        async with async_session_maker() as session:
            # 1. Simple select 1
            res = await session.execute(text("SELECT 1"))
            print(f"Connection OK: {res.scalar()}")
            
            # 2. Check Users
            result = await session.execute(select(User))
            users = result.scalars().all()
            print(f"Found {len(users)} users.")
            for u in users:
                print(f"  - {u.discord_username} (ID: {u.id}, DiscordID: {u.discord_id})")
                
            # 3. Check for duplicates
            discord_ids = [u.discord_id for u in users]
            if len(discord_ids) != len(set(discord_ids)):
                print("!! CRITICIAL: Duplicate Discord IDs found !!")
            else:
                print("No duplicates found.")
                
    except Exception as e:
        print(f"DB Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_db())
