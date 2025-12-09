
import asyncio
import os
import sys
from sqlalchemy import select
from src.db.session import async_session_factory
from src.db.models import RehearsalSchedule, Script, ProjectMember, User, TheaterProject

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_data():
    async with async_session_factory() as db:
        print("Checking RehearsalSchedules...")
        result = await db.execute(select(RehearsalSchedule))
        schedules = result.scalars().all()
        
        for s in schedules:
            print(f"Schedule ID: {s.id}, Project ID: {s.project_id}, Script ID: {s.script_id}")
            
            # Check if script exists
            script_res = await db.execute(select(Script).where(Script.id == s.script_id))
            script = script_res.scalar_one_or_none()
            print(f"  -> Linked Script found: {script is not None}")
            if script:
                print(f"     Script Title: {script.title}")
            else:
                print("     [ERROR] Script missing!")

        print("\nChecking Projects...")
        result = await db.execute(select(TheaterProject))
        projects = result.scalars().all()
        for p in projects:
            print(f"Project ID: {p.id}, Name: {p.name}")
            # Count schedules
            sched_res = await db.execute(select(RehearsalSchedule).where(RehearsalSchedule.project_id == p.id))
            scheds = sched_res.scalars().all()
            print(f"  -> Schedules count: {len(scheds)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_data())
