
import asyncio
import os
import sys

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from src.db.session import async_session_factory
from src.db.models import RehearsalSchedule, Script, TheaterProject

async def check_data():
    async with async_session_factory() as db:
        print("--- Scripts ---")
        # Search for the specific script
        query = select(Script).where(Script.title.like("%ラブコメ%"))
        result = await db.execute(query)
        scripts = result.scalars().all()
        
        target_script_id = None
        if scripts:
            for s in scripts:
                print(f"Found Script: ID={s.id}, Title='{s.title}'")
                target_script_id = s.id
        else:
            print("No script found matching 'ラブコメ'.")

        print("\n--- Rehearsal Schedules ---")
        result = await db.execute(select(RehearsalSchedule))
        schedules = result.scalars().all()
        
        for s in schedules:
            print(f"Schedule ID={s.id}, Script ID={s.script_id}")
            # Check correctness
            script_res = await db.execute(select(Script).where(Script.id == s.script_id))
            linked_script = script_res.scalar_one_or_none()
            if linked_script:
                print(f"  -> OK. Linked to '{linked_script.title}'")
            else:
                print(f"  -> ERROR. Script ID {s.script_id} NOT FOUND.")
                if target_script_id:
                     print(f"  -> PROPOSAL: Should this be linked to {target_script_id}?")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_data())
