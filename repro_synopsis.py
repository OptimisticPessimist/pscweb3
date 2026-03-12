
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
from src.db.models import Script, Scene, Line, Character
from src.services.fountain_parser import parse_fountain_and_create_models

async def repro():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        script = Script(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            title="Repro Script",
            content=""
        )
        session.add(script)
        await session.commit()
        
        fountain_content = """Title: Preservation Test

# あらすじ
= 1行目のあらすじ
= 2行目のあらすじ

BRICK
(whispering)
Hello in synopsis.

Parenthetical in synopsis as action.

## シーン1
通常ト書き

BRICK
(whispering)
Hello.

> CUT TO:
"""
        await parse_fountain_and_create_models(script, fountain_content, session)
        
        # Also inspect what the Fountain library sees (with preprocessing)
        from fountain.fountain import Fountain
        from src.utils.fountain_utils import preprocess_fountain
        f_raw = preprocess_fountain(fountain_content)
        f = Fountain(f_raw)
        print("\n--- Preprocessed Fountain Elements ---")
        for i, element in enumerate(f.elements):
            print(f"[{i}] {element.element_type}: {repr(element.original_content)}")
        print("--------------------------------------\n")
        
        # Verify
        from sqlalchemy import select
        result = await session.execute(select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number))
        scenes = result.scalars().all()
        
        for scene in scenes:
            print(f"Scene #{scene.scene_number}: {scene.heading}")
            print(f"Description: {scene.description}")
            result_lines = await session.execute(select(Line).where(Line.scene_id == scene.id).order_by(Line.order))
            lines = result_lines.scalars().all()
            print(f"Lines count: {len(lines)}")
            for line in lines:
                print(f"  Line: {line.content}")

if __name__ == "__main__":
    asyncio.run(repro())
