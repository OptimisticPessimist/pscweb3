import pytest
from src.services.fountain_parser import parse_fountain_and_create_models

def test_scene_numbering_with_section_heading():
    fountain_content = """# Section 1
.SCENE 1
Action here.
"""
    # Force mock project_id
    project_id = "test-project"
    
    # Normally this would need a DB session, but the parser returns models.
    # We can check the models returned.
    from sqlalchemy.ext.asyncio import AsyncSession
    from unittest.mock import MagicMock
    
    # Actually, let's just use the parser logic to see how it assigns scene numbers.
    # The models objects will have scene_number set.
    
    # We need to provide a mock db if it calls db.add/commit, but wait, 
    # parse_fountain_and_create_models takes current_user and project_id and db.
    
    # Let's see the signature of parse_fountain_and_create_models
    pass

@pytest.mark.asyncio
async def test_scene_numbering_real(db):
    from src.db.models import TheaterProject, User, Script, Scene
    from src.services.fountain_parser import parse_fountain_and_create_models
    from sqlalchemy import select
    
    project = TheaterProject(name="Test Project")
    db.add(project)
    user = User(discord_id="parser-user", discord_username="parser")
    db.add(user)
    await db.flush()
    
    script = Script(project_id=project.id, uploaded_by=user.id, title="Test Script", content="")
    db.add(script)
    await db.commit()

    fountain_content = """## Section 1
.SCENE 1
Action here.

## Section 2
.SCENE 2
Action again.
"""
    await parse_fountain_and_create_models(
        script, fountain_content, db
    )
    await db.commit()
    
    # Reload scenes
    result = await db.execute(
        select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number)
    )
    scenes = result.scalars().all()
    for s in scenes:
        print(f"DEBUG: Scene {s.scene_number}, Heading: {s.heading}")
    
    # Check scene numbering
    assert len(scenes) == 2
    assert scenes[0].scene_number == 1
    assert scenes[1].scene_number == 2
    
    # Check headings (merged Section + Scene)
    assert scenes[0].heading == "Section 1 (SCENE 1)"
    assert scenes[1].heading == "Section 2 (SCENE 2)"

@pytest.mark.asyncio
async def test_scene_numbering_with_blank_lines(db):
    from src.db.models import TheaterProject, User, Script, Scene
    from src.services.fountain_parser import parse_fountain_and_create_models
    from sqlalchemy import select
    
    project = TheaterProject(name="Test Project")
    db.add(project)
    user = User(discord_id="parser-user-2", discord_username="parser2")
    db.add(user)
    await db.flush()
    
    script = Script(project_id=project.id, uploaded_by=user.id, title="Test Script", content="")
    db.add(script)
    await db.commit()

    fountain_content = """## Section 1

.SCENE 1

Action here.
"""
    await parse_fountain_and_create_models(
        script, fountain_content, db
    )
    await db.commit()
    
    # Reload scenes
    result = await db.execute(
        select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number)
    )
    scenes = result.scalars().all()
    
    assert len(scenes) == 1
    assert scenes[0].scene_number == 1
    assert scenes[0].heading == "Section 1 (SCENE 1)"
