
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv("backend/.env")

from src.db.models import Script, Scene

async def check_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found")
        return

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Get the latest 3 scripts
        stmt = select(Script).order_by(Script.uploaded_at.desc()).limit(3)
        result = await session.execute(stmt)
        scripts = result.scalars().all()

        for script in scripts:
            print(f"\n========================================")
            print(f"Script: {script.title}")
            print(f"ID: {script.id}")
            print(f"Uploaded: {script.uploaded_at}")
            print(f"Revision: {script.revision}")
            print(f"Notes (metadata): {repr(script.notes)}")
            print(f"Author: {script.author}")
            print(f"Draft Date: {script.draft_date}")
            
            # Check for scene 0 (Synopsis)
            scene_stmt = select(Scene).where(Scene.script_id == script.id, Scene.scene_number == 0)
            scene_result = await session.execute(scene_stmt)
            synopsis_scenes = scene_result.scalars().all()

            if not synopsis_scenes:
                print(">>> RESULT: No Scene #0 found.")
                
                # Check if maybe it's the first scene but number is not 0?
                any_scene_stmt = select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number).limit(1)
                any_scene_res = await session.execute(any_scene_stmt)
                first_scene = any_scene_res.scalar_one_or_none()
                if first_scene:
                    print(f"First Scene found at number {first_scene.scene_number}: {first_scene.heading}")
                    print(f"Description (first 200 chars): {repr(first_scene.description[:200])}")
            else:
                for idx, scene in enumerate(synopsis_scenes):
                    print(f">>> RESULT: Scene #0 [{idx}] found (ID: {scene.id})")
                    print(f"Heading: {scene.heading}")
                    print("Description:")
                    print("-" * 20)
                    print(scene.description if scene.description else "(Empty)")
                    print("-" * 20)
                    if scene.description and "\n" in scene.description:
                        line_count = len(scene.description.splitlines())
                        print(f"Status: Contains {line_count} lines.")
                    else:
                        print("Status: Single line or empty.")

if __name__ == "__main__":
    asyncio.run(check_db())
