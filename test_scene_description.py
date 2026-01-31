
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from src.services.fountain_parser import parse_fountain_and_create_models
from src.db.models import Script, Base

# Mock DB setup (using sqlite for testing)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

async def test_scene_description():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Create a dummy script
        script = Script(
            title="Test Script",
            content="",
            uploaded_by=None # Hack: bypassing FK constraint or need to create user?
            # SQLite might enforce FK if enabled. Let's try to mock User if needed.
        )
        # Actually in SQLite FK logic depends on configuration, often disabled by default in simple connection.
        # But Base.metadata.create_all might set it up.
        # Let's create a user just in case.
        from src.db.models import User, TheaterProject
        import uuid
        user = User(id=uuid.uuid4(), discord_id="test_id", discord_username="test_user")
        db.add(user)
        
        project = TheaterProject(id=uuid.uuid4(), name="Test Project")
        db.add(project)
        await db.flush()
        
        script.uploaded_by = user.id
        script.project_id = project.id
        db.add(script)
        await db.flush()

        fountain_content = """
Title: Scene Test

# Act 1

INT. SCENE 1 - DAY

This is a description of the scene.
It explains what happens.

@CHARACTER
Dialogue.

INT. SCENE 2 - NIGHT

Another description.
"""
        print("Parsing fountain content...")
        try:
            await parse_fountain_and_create_models(script, fountain_content, db)
        except Exception as e:
            print(f"Error checking scenes: {e}")
            import traceback
            traceback.print_exc()
            return

        print("Checking Scenes...")
        # Check generated scenes
        from sqlalchemy import select
        from src.db.models import Scene
        result = await db.execute(select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number))
        scenes = result.scalars().all()
        
        for scene in scenes:
            print(f"Scene {scene.scene_number}: {scene.heading}")
            print(f"  Description: '{scene.description}'")
            if scene.description is None:
                print("  [FAIL] Description is None")
            else:
                print(f"  [PASS] Description found: {scene.description}")

if __name__ == "__main__":
    asyncio.run(test_scene_description())
