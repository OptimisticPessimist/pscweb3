import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.db.models import Base, Script, TheaterProject, User
from src.services.fountain_parser import parse_fountain_and_create_models
from src.services.scene_chart_generator import generate_scene_chart

# Mock Setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def debug_upload():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Create Dummy Data
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        
        # User & Project are needed for foreign keys? 
        # Actually Script has FK to Project and User.
        # But for 'parse' logic, we just need script instance.
        
        # Create User
        user = User(id=user_id, email="test@example.com", username="testuser", discord_id="123", avatar_url="http://test")
        db.add(user)
        
        # Create Project
        project = TheaterProject(id=project_id, name="Test Project", description="Desc", created_by=user_id)
        db.add(project)
        
        await db.commit()
        
        # Create Script
        script_id = uuid.uuid4()
        script = Script(
            id=script_id,
            project_id=project_id,
            uploaded_by=user_id,
            title="Test Script",
            content="""Title: Test
Author: Me

INT. TEST - DAY

CHARACTER
Hello.
""",
            is_public=False
        )
        db.add(script)
        await db.commit()
        await db.refresh(script)

        print("--- Starting Parse ---")
        try:
            await parse_fountain_and_create_models(script, script.content, db)
            print("--- Parse Success ---")
        except Exception as e:
            print(f"--- Parse Failed: {e}")
            import traceback
            traceback.print_exc()
            return

        print("--- Starting Chart Gen ---")
        # Important: In real code, we don't refresh script.scenes?
        # Let's inspect what happens here.
        # If I don't refresh, script.scenes might be empty or detached?
        # But 'expire_on_commit=False' is used in app? Default is True.
        # In `src/db/__init__.py`, let's check config.
        # Assuming defaults.
        
        try:
            # Emulate the call in scripts.py
            # Note: script object is same instance.
            
            # To simulate exact condition, we might need to manually trigger loading scenes if they aren't loaded.
            # But wait, parse_fountain adds scenes to DB. 
            # Does `script.scenes` reflect that? No, unless we refresh.
            
            # Note: If generate_scene_chart fails because script.scenes is empty, it just returns empty chart.
            # Does it fail?
            await generate_scene_chart(script, db)
            print("--- Chart Gen Success ---")
        except Exception as e:
            print(f"--- Chart Gen Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_upload())
