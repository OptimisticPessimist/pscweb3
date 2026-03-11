from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.projects import ProjectCreate, create_project
from src.config import settings
from src.db.models import User
from src.services.premium_config import PremiumConfigService


@pytest.mark.asyncio
async def test_api_create_premium_project(db: AsyncSession):
    await PremiumConfigService.refresh_config()

    # 1. Setup User with premium password
    test_password = settings.premium_password_test
    print(f"Test password: {test_password}")

    user = User(
        discord_id=str(uuid4())[:20],
        discord_username="premium_tester",
        premium_password=test_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Mocking background tasks and discord service
    from unittest.mock import MagicMock

    bg_tasks = MagicMock()
    discord_svc = MagicMock()

    # Create 1st project (should succeed)
    project_data = ProjectCreate(
        name="Project 1",
        description="test",
        is_public=False,
        attendance_reminder_1_hours=48,
        attendance_reminder_2_hours=24,
    )
    p1 = await create_project(project_data, bg_tasks, user, db, discord_svc)
    assert p1 is not None

    # Create 2nd project (should succeed for premium 999)
    project_data2 = ProjectCreate(
        name="Project 2",
        description="test",
        is_public=False,
        attendance_reminder_1_hours=48,
        attendance_reminder_2_hours=24,
    )
    try:
        p2 = await create_project(project_data2, bg_tasks, user, db, discord_svc)
        print("Success! Created 2nd project via API handler.")
    except Exception as e:
        print(f"Failed to create 2nd project! Exception: {e}")
        raise e
