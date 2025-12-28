import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import User, TheaterProject, ProjectMember, Milestone, Reservation
from datetime import datetime
from src.main import app
from src.dependencies.auth import get_current_user_dep

@pytest.mark.asyncio
async def test_list_milestones_with_capacity(client: AsyncClient, db: AsyncSession, test_project: TheaterProject, test_user: User):
    # Setup: 1 Milestone, 2 Reservations
    ms = Milestone(
        project_id=test_project.id,
        title="Capacity Test",
        start_date=datetime.now(),
        reservation_capacity=20
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    
    r1 = Reservation(milestone_id=ms.id, name="A", email="a@a.com", count=3)
    r2 = Reservation(milestone_id=ms.id, name="B", email="b@b.com", count=5)
    db.add_all([r1, r2])
    await db.commit()
    
    # Auth
    app.dependency_overrides[get_current_user_dep] = lambda: test_user
    
    try:
        response = await client.get(f"/api/projects/{test_project.id}/milestones")
        assert response.status_code == 200
        data = response.json()
        
        # Find our milestone
        target = next((m for m in data if m["id"] == str(ms.id)), None)
        assert target is not None
        assert target["current_reservation_count"] == 8  # 3 + 5
        assert target["reservation_capacity"] == 20
    finally:
        del app.dependency_overrides[get_current_user_dep]

@pytest.mark.asyncio
async def test_update_milestone_capacity(client: AsyncClient, db: AsyncSession, test_project: TheaterProject, test_user: User):
    ms = Milestone(
        project_id=test_project.id,
        title="Update Test",
        start_date=datetime.now(),
        reservation_capacity=10
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    
    # Auth
    app.dependency_overrides[get_current_user_dep] = lambda: test_user
    
    try:
        payload = {"reservation_capacity": 50}
        response = await client.patch(f"/api/projects/{test_project.id}/milestones/{ms.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["reservation_capacity"] == 50
        assert data["title"] == "Update Test" # Unchanged
        
        # Verify DB
        await db.refresh(ms)
        assert ms.reservation_capacity == 50
    finally:
        del app.dependency_overrides[get_current_user_dep]
