import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Rehearsal, AttendanceEvent, RehearsalSchedule, Script, Scene, RehearsalScene, ProjectMember
from src.services.discord import get_discord_service
from src.main import app
from datetime import datetime, timedelta, timezone

# Mock Discord Service
async def mock_get_discord_service():
    class MockDiscordService:
        async def send_message(self, channel_id, content=None, embed=None, components=None):
            return {"id": "mock_msg_id", "channel_id": channel_id}
        
    return MockDiscordService()

@pytest.fixture(scope="function")
def override_discord_service():
    app.dependency_overrides[get_discord_service] = mock_get_discord_service
    yield
    app.dependency_overrides.pop(get_discord_service, None)

@pytest.mark.asyncio
async def test_add_rehearsal_success(
    client: AsyncClient, 
    db: AsyncSession, 
    test_user_token: str, 
    test_project,
    override_discord_service
):
    # 1. Setup Data
    # Script & Scene
    script = Script(project_id=test_project.id, title="Test Script")
    db.add(script)
    await db.flush()
    
    scene1 = Scene(script_id=script.id, scene_number=1, heading="Scene 1")
    scene2 = Scene(script_id=script.id, scene_number=2, heading="Scene 2")
    db.add_all([scene1, scene2])
    
    # Schedule
    schedule = RehearsalSchedule(
        project_id=test_project.id, 
        script_id=script.id,
        created_at=datetime.now() # Naive for sqlite compatibility
    )
    db.add(schedule)
    
    await db.commit()
    await db.refresh(schedule)
    await db.refresh(scene1)
    await db.refresh(scene2)
    
    # 2. Add Rehearsal Request
    valid_payload = {
        "date": "2025-12-12T10:00:00+09:00", # Aware
        "duration_minutes": 120,
        "location": "Studio A",
        "notes": "Test Rehearsal",
        "scene_ids": [str(scene1.id), str(scene2.id)],
        "create_attendance_check": True,
        "attendance_deadline": "2025-12-11T08:00:00+09:00", # Aware
        "participants": [], # Default to all members
        "casts": []
    }
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.post(
        f"/api/rehearsals/{schedule.id}", 
        json=valid_payload, 
        headers=headers
    )
    
    # 3. Verify Response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["location"] == "Studio A"
    assert len(data["scenes"]) == 2 # Assuming response includes scenes or scene_ids
    
    # 4. Verify DB - Rehearsal
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == data["id"]))
    rehearsal = result.scalar_one()
    # Check naive date storage (if model is naive)
    # The API might return it as is, depending on Pydantic config.
    # But DB should successfully store it.
    
    # Verify Rehearsal-Scene Link
    result = await db.execute(select(RehearsalScene).where(RehearsalScene.rehearsal_id == rehearsal.id))
    links = result.scalars().all()
    assert len(links) == 2
    
    # 5. Verify DB - AttendanceEvent
    # AttendanceEvent is created via background task or await? Code was changed to await.
    result = await db.execute(
        select(AttendanceEvent).where(AttendanceEvent.title.like("稽古%"))
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.completed is False
    # Check Deadline Naivety (DB column is naive, passed value was naive)
    # If we fetch it, sqlalchemy returns datetime.
    # It should match the naive version of input.
    # Input: 2025-12-11 08:00 +09:00 -> Naive: 2025-12-11 08:00
    assert event.deadline.hour == 8
    assert event.deadline.day == 11
    assert event.deadline.tzinfo is None # Should be naive
