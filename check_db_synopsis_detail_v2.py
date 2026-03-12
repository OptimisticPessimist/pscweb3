
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

    # Disable statement cache for PgBouncer/Supabase
    engine = create_async_engine(
        database_url,
        connect_args={"statement_cache_size": 0}
    )
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Get the latest 5 scripts to be sure
        stmt = select(Script).order_by(Script.uploaded_at.desc()).limit(5)
        result = await session.execute(stmt)
        scripts = result.scalars().all()

        for script in scripts:
            print(f"\n========================================")
            print(f"Script: {script.title}")
            print(f"ID: {script.id}")
            print(f"Uploaded: {script.uploaded_at}")
            print(f"Revision: {script.revision}")
            print(f"Notes: {repr(script.notes)}")
            
            # Check for scene 0 (Synopsis)
            scene_stmt = select(Scene).where(Scene.script_id == script.id, Scene.scene_number == 0)
            scene_result = await session.execute(scene_stmt)
            synopsis_scenes = scene_result.scalars().all()

            if not synopsis_scenes:
                print(">>> RESULT: No Scene #0 (Synopsis) found.")
                
                # Check for other scenes to see how it was parsed
                any_scene_stmt = select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number).limit(1)
                any_scene_res = await session.execute(any_scene_stmt)
                first = any_scene_res.scalar_one_or_none()
                if first:
                    print(f"First parsed scene is #{first.scene_number}: {first.heading}")
                    print(f"Description: {repr(first.description)}")
            else:
                for idx, scene in enumerate(synopsis_scenes):
                    print(f">>> RESULT: Scene #0 [{idx}] found")
                    print(f"Description (repr):\n{repr(scene.description)}")

if __name__ == "__main__":
    asyncio.run(check_db())
