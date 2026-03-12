
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
        # Get the latest script
        stmt = select(Script).order_by(Script.uploaded_at.desc()).limit(5)
        result = await session.execute(stmt)
        scripts = result.scalars().all()

        for script in scripts:
            print(f"\n--- Script: {script.title} (ID: {script.id}) ---")
            print(f"Uploaded at: {script.uploaded_at}")
            
            # Check for scene 0 (Synopsis)
            scene_stmt = select(Scene).where(Scene.script_id == script.id, Scene.scene_number == 0)
            scene_result = await session.execute(scene_stmt)
            synopsis_scenes = scene_result.scalars().all()

            if not synopsis_scenes:
                print("No Synopsis scene (Scene #0) found.")
                continue

            for scene in synopsis_scenes:
                print(f"Synopsis Scene ID: {scene.id}")
                print(f"Heading: {scene.heading}")
                print("Description:")
                print(repr(scene.description))
                if scene.description and "\n" in scene.description:
                    print("Status: Contains multiple lines.")
                else:
                    print("Status: Single line or empty.")

if __name__ == "__main__":
    asyncio.run(check_db())
