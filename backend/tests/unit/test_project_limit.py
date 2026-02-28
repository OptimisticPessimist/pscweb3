import pytest
from uuid import uuid4
from fastapi import HTTPException
from src.services.project_limit import check_project_limit
from src.db.models import TheaterProject, ProjectMember, Script, User

# Helper functions
async def create_user(db, username="test_user"):
    user = User(discord_id=str(uuid4())[:20], discord_username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_project(db, owner, name="Test Project"):
    project = TheaterProject(name=name, created_by_id=owner.id)
    db.add(project)
    await db.flush()
    member = ProjectMember(project_id=project.id, user_id=owner.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(project)
    return project

@pytest.mark.asyncio
async def test_check_project_limit_allows_under_limit(db):
    user = await create_user(db)
    
    # Check limit for new private project -> Total 1 -> OK
    await check_project_limit(user.id, db, new_project_is_public=False)

@pytest.mark.asyncio
async def test_check_project_limit_allows_public_project(db):
    user = await create_user(db)
    await create_project(db, user) # 1st
    
    # Check limit for new PUBLIC project -> Total private 1, public 1 -> OK
    await check_project_limit(user.id, db, new_project_is_public=True)

@pytest.mark.asyncio
async def test_check_project_limit_blocks_over_limit_private(db):
    user = await create_user(db)
    await create_project(db, user) # 1st
    
    # Check limit for new private project -> Total 2 -> Error
    with pytest.raises(HTTPException) as excinfo:
        await check_project_limit(user.id, db, new_project_is_public=False)
    assert excinfo.value.status_code == 400
    assert "作成枠" in excinfo.value.detail

@pytest.mark.asyncio
async def test_check_project_limit_excludes_existing_public_projects(db):
    user = await create_user(db)
    
    public_project = await create_project(db, user) # 1st (will be public)
    public_project.is_public = True # Explicitly set public
    
    # Add public script to make it public (optional if we set project.is_public)
    script = Script(
        id=uuid4(),
        project_id=public_project.id,
        uploaded_by=user.id,
        title="Public Script",
        content=".",
        is_public=True
    )
    db.add(script)
    await db.commit()
    await db.refresh(public_project) # Ensure relationship is loaded if needed, though check_project_limit queries it fresh
    
    # Current private count = 0. New private project -> Total 1 -> OK
    await check_project_limit(user.id, db, new_project_is_public=False)
    
    # Add a private project to reach limit
    await create_project(db, user) # 2nd project (Private)
    # Total projects: 2. Private: 1 (2nd). Public: 1 (1st).
    
    # now private count = 1. New private project should fail
    with pytest.raises(HTTPException):
        await check_project_limit(user.id, db, new_project_is_public=False)

@pytest.mark.asyncio
async def test_check_project_limit_loophole_prevention(db):
    user = await create_user(db)
    await create_project(db, user) # 1st Private
    
    p_public = await create_project(db, user) # 2nd (Public)
    script = Script(
        id=uuid4(),
        project_id=p_public.id,
        uploaded_by=user.id,
        title="Public Script",
        content=".",
        is_public=True
    )
    db.add(script)
    await db.commit()
    
    # Try to update p_public to private (is_public=False)
    with pytest.raises(HTTPException) as excinfo:
        await check_project_limit(
            user.id, 
            db, 
            project_id_to_exclude=p_public.id, 
            new_project_is_public=False
        )
    assert excinfo.value.status_code == 400
