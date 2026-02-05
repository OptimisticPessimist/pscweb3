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
    project = TheaterProject(name=name)
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
    await create_project(db, user) # 1st project (Private)
    
    # Check limit for new private project -> Total 2 -> OK
    await check_project_limit(user.id, db, new_project_is_public=False)

@pytest.mark.asyncio
async def test_check_project_limit_allows_public_project(db):
    user = await create_user(db)
    await create_project(db, user) # 1st
    await create_project(db, user) # 2nd
    
    # Check limit for new PUBLIC project -> Total private 2, public 1 -> OK
    await check_project_limit(user.id, db, new_project_is_public=True)

@pytest.mark.asyncio
async def test_check_project_limit_blocks_over_limit_private(db):
    user = await create_user(db)
    await create_project(db, user) # 1st
    await create_project(db, user) # 2nd
    
    # Check limit for new private project -> Total 3 -> Error
    with pytest.raises(HTTPException) as excinfo:
        await check_project_limit(user.id, db, new_project_is_public=False)
    assert excinfo.value.status_code == 400
    assert "作成上限" in excinfo.value.detail

@pytest.mark.asyncio
async def test_check_project_limit_excludes_existing_public_projects(db):
    user = await create_user(db)
    await create_project(db, user) # 1st Private
    
    public_project = await create_project(db, user) # 2nd (will be public)
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
    
    # Current private count = 1. New private project -> Total 2 -> OK
    await check_project_limit(user.id, db, new_project_is_public=False)
    
    # Add another private project to reach limit
    await create_project(db, user) # 3rd project (Private)
    # Total projects: 3. Private: 2 (1st and 3rd). Public: 1 (2nd).
    
    # now private count = 2. New private project should fail
    with pytest.raises(HTTPException):
        await check_project_limit(user.id, db, new_project_is_public=False)

@pytest.mark.asyncio
async def test_check_project_limit_loophole_prevention(db):
    user = await create_user(db)
    await create_project(db, user) # 1st Private
    await create_project(db, user) # 2nd Private
    
    p_public = await create_project(db, user) # 3rd (Public)
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
