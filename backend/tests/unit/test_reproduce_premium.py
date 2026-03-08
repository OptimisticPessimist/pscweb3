import pytest
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.project_limit import check_project_limit
from src.services.premium_config import PremiumConfigService
from src.db.models import TheaterProject, ProjectMember, User
from src.config import settings

# Helper functions
async def create_user(db, username="test_limit_user", premium_password=None):
    user = User(discord_id=str(uuid4())[:20], discord_username=username, premium_password=premium_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_project(db, owner, is_public=False):
    project = TheaterProject(name="Test Project", is_public=is_public, created_by_id=owner.id)
    db.add(project)
    await db.flush()
    member = ProjectMember(project_id=project.id, user_id=owner.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(project)
    return project

@pytest.mark.asyncio
async def test_premium_user_can_exceed_default_limit(db: AsyncSession):
    # Setup premium config for test
    # Ensure PremiumConfigService has the right config in memory
    await PremiumConfigService.refresh_config()
    
    # 1. Setup User with premium password
    test_password = settings.premium_password_test
    print(f"Test password: {test_password}")
    
    user = await create_user(db, premium_password=test_password)
    
    # 2. Create 1 Private Project (Default limit is 1)
    await create_project(db, user, is_public=False)
    
    # 3. Create another Private Project
    # This should succeed without raising HTTPException because limit is 99
    try:
        await check_project_limit(user.id, db, new_project_is_public=False)
        print("Success! Premium limit is working in tests.")
    except Exception as e:
        print(f"Failed! Exception: {e}")
        raise e
