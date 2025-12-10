import asyncio
import os
import sys

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_root)

from sqlalchemy import select

from src.db import get_db
from src.db.models import SceneChart, Script


async def main():
    async for db in get_db():
        print("Checking for missing Scene Charts...")
        result = await db.execute(select(Script))
        scripts = result.scalars().all()

        for script in scripts:
            result = await db.execute(select(SceneChart).where(SceneChart.script_id == script.id))
            chart = result.scalar_one_or_none()


            if not chart:
                print(f"Generating chart for Script {script.id} ({script.title})...")
                # ... (generation code)
            else:
                # Count mappings
                result = await db.execute(select(SceneChart).where(SceneChart.id == chart.id))
                # Need to load mappings relationship or query SceneCharacterMapping
                from src.db.models import SceneCharacterMapping
                result = await db.execute(select(SceneCharacterMapping).where(SceneCharacterMapping.chart_id == chart.id))
                mappings = result.scalars().all()
                print(f"Script {script.id}: Chart exists with {len(mappings)} mappings.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
