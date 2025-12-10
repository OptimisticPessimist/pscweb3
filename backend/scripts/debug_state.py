import asyncio
import os
import sys

# Add backend root to sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_root)

# Force re-import of src to ensure we get the right one
if 'src' in sys.modules:
    del sys.modules['src']

from sqlalchemy import select

from src.db import get_db
from src.db.models import RehearsalSchedule, SceneChart, Script, TheaterProject


async def main():
    async for db in get_db():
        print("Checking DB State...")

        # Check Projects
        result = await db.execute(select(TheaterProject))
        projects = result.scalars().all()
        print(f"Projects count: {len(projects)}")

        for p in projects:
            print(f"Project: {p.id} ({p.name})")

            # Check Scripts
            result = await db.execute(select(Script).where(Script.project_id == p.id))
            scripts = result.scalars().all()
            print(f"  Scripts: {len(scripts)}")

            for s in scripts:
                print(f"    Script: {s.id} ({s.title})")

                # Check SceneChart
                result = await db.execute(select(SceneChart).where(SceneChart.script_id == s.id))
                chart = result.scalar_one_or_none()
                print(f"      SceneChart: {'FOUND' if chart else 'MISSING'}")

            # Check RehearsalSchedule
            result = await db.execute(select(RehearsalSchedule).where(RehearsalSchedule.project_id == p.id))
            schedule = result.scalar_one_or_none()
            print(f"  RehearsalSchedule: {'FOUND' if schedule else 'MISSING'}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
