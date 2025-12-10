
import asyncio
import os
import sys

# Add backend directory to python path
# Assuming we run this from f:\src\PythonProject\pscweb3-1\backend
sys.path.append(os.getcwd())

from sqlalchemy import select
from src.db.session import async_session_factory

from src.db.models import Script


async def find_script():
    async with async_session_factory() as db:
        print("Searching for script...")
        query = select(Script).where(Script.title.like("%ラブコメ%"))
        result = await db.execute(query)
        scripts = result.scalars().all()

        if not scripts:
            print("No script found.")
            return

        for s in scripts:
            print(f"SCRIPT_FOUND: ID={s.id}, Title='{s.title}', ProjectID={s.project_id}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(find_script())
