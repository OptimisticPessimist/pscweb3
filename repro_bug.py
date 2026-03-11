
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Mock models for testing purposes if we can't easily import from src.db.models
# But it's better to try importing them first.
import sys
import os
sys.path.append(os.getcwd())

from src.db.models import Base, Script, Scene, Character, Line, TheaterProject, User
from src.services.fountain_parser import parse_fountain_and_create_models

async def test_repro():
    # Setup in-memory sqlite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with Session() as session:
        # Create dummy project and script
        user = User(discord_id="12345", discord_username="testuser")
        session.add(user)
        await session.flush()
        
        project = TheaterProject(name="Test Project", created_by_id=user.id)
        session.add(project)
        await session.flush()
        
        script = Script(
            project_id=project.id,
            uploaded_by=user.id,
            title="Repro Script",
            content=""
        )
        session.add(script)
        await session.flush()
        
        fountain_content = """
# あらすじ

ト書き1
改行を含む内容。

@キャラA
セリフ1

ト書き2
さらに続く。
        """
        
        try:
            await parse_fountain_and_create_models(script, fountain_content, session)
            await session.commit()
            print("Successfully parsed and committed.")
            
            # Verify data
            from sqlalchemy import select
            res = await session.execute(select(Scene).where(Scene.script_id == script.id))
            scenes = res.scalars().all()
            for s in scenes:
                print(f"Scene {s.scene_number}: {s.heading}")
                print(f"Description:\n{s.description}")
                
            res = await session.execute(select(Line).where(Line.scene_id.in_([s.id for s in scenes])))
            lines = res.scalars().all()
            print(f"Total lines: {len(lines)}")
            for l in lines:
                print(f"Line {l.order}: {l.content}")
                
        except Exception as e:
            print(f"Caught exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_repro())
