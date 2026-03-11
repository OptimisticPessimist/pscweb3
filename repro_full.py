
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.db.models import Base, Script, Scene, Character, Line, TheaterProject, User, ProjectMember
from src.services.script_processor import process_script_upload

async def test_full_flow():
    # Setup in-memory sqlite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with Session() as session:
        # Create user
        user = User(discord_id="123456", discord_username="testuser")
        session.add(user)
        await session.flush()
        
        # Create project
        project = TheaterProject(name="Test Project", created_by_id=user.id)
        session.add(project)
        await session.flush()
        
        # Create member
        member = ProjectMember(project_id=project.id, user_id=user.id, role="owner")
        session.add(member)
        await session.flush()
        
        fountain_content = """
Title: Test Script
Author: Test Author

# あらすじ

ト書き1
改行。

@CHAR
セリフ1

ト書き2

# シーン1
ト書き3
        """
        
        try:
            print("Starting process_script_upload...")
            script, is_update = await process_script_upload(
                project_id=project.id,
                user_id=user.id,
                title="Test Script",
                author="Test Author",
                fountain_text=fountain_content,
                is_public=False,
                db=session
            )
            print("Starting process_script_upload (update)...")
            script, is_update = await process_script_upload(
                project_id=project.id,
                user_id=user.id,
                title="Test Script Updated",
                author="Test Author",
                fountain_text=fountain_content + "\n# シーン2\n追加シーン",
                is_public=False,
                db=session
            )
            print(f"Success! is_update={is_update}")
            print(f"Script scenes: {len(script.scenes)}")
            for s in script.scenes:
                print(f"Scene {s.scene_number} heading: {s.heading}")
                print(f"Description length: {len(s.description) if s.description else 0}")
                
        except Exception as e:
            print(f"Caught exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_flow())
