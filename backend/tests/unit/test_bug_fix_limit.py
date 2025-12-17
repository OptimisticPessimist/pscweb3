import pytest
from uuid import uuid4
from fastapi import HTTPException
from src.services.project_limit import check_project_limit
from src.db.models import TheaterProject, ProjectMember, Script, User

# Helper functions
async def create_user(db, username="test_limit_user"):
    user = User(discord_id=str(uuid4())[:20], discord_username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_private_project(db, owner):
    project = TheaterProject(name="Private Project", is_public=False)
    db.add(project)
    await db.flush()
    member = ProjectMember(project_id=project.id, user_id=owner.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(project)
    return project

async def create_public_script(db, uploader):
    # Public project for the script
    project = TheaterProject(name="Source Public Project", is_public=True)
    db.add(project)
    await db.flush()
    
    script = Script(
        project_id=project.id,
        uploaded_by=uploader.id,
        title="Public Source Script",
        content=".",
        is_public=True
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)
    return script

@pytest.mark.asyncio
async def test_import_script_respects_private_limit(db):
    """
    Test that importing a script creates a PRIVATE project (as per policy),
    and thus should be blocked if the user already has 2 private projects.
    
    Before Fix: import_script creates PUBLIC project -> API returns 200 OK (Test Fails)
    After Fix: import_script creates PRIVATE project -> API returns 400 Bad Request (Test Passes)
    """
    # 1. Setup User
    user = await create_user(db)
    
    # 2. Create 2 Private Projects (Limit Reached)
    await create_private_project(db, user)
    await create_private_project(db, user)
    
    # 3. Create a Public Script to import from
    source_script = await create_public_script(db, user)
    
    # 4. Call import_script logic directly (simulating API controller logic)
    # We can invoke the controller function or simulate the logic.
    # Since we are in a unit test valid for DB interaction, let's call the API handler if possible,
    # or replicate the core logic we are testing.
    # Calling the API handler is better but requires mocking dependencies (BackgroundTasks etc).
    # For simplicity in this targeted test, we'll verify the BEHAVIOR via the service logic check 
    # that we intend to add/modify.
    
    from src.api.projects import import_script
    from unittest.mock import MagicMock
    
    # Mock constraints
    background_tasks = MagicMock()
    discord_service = MagicMock()
    
    # 5. Expectation: Should raise HTTPException(400) because it SHOULD try to create a private project
    with pytest.raises(HTTPException) as excinfo:
        await import_script(
            script_id=source_script.id,
            background_tasks=background_tasks,
            current_user=user,
            db=db,
            discord_service=discord_service
        )
    
    assert excinfo.value.status_code == 400
    assert "作成上限" in excinfo.value.detail
