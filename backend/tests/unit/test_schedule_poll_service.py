import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from src.db.models import SchedulePoll, SchedulePollCandidate, SchedulePollAnswer
from src.services.schedule_poll_service import SchedulePollService
from src.services.discord import DiscordService

@pytest.fixture
def mock_discord_service():
    service = MagicMock(spec=DiscordService)
    service.send_channel_message = AsyncMock(return_value={"id": "mock_msg_id"})
    return service

@pytest.mark.asyncio
async def test_schedule_poll_creation(db, mock_discord_service, test_project, test_user):
    service = SchedulePollService(db, mock_discord_service)
    
    candidates = [
        {"start_datetime": datetime.now(timezone.utc), "end_datetime": datetime.now(timezone.utc) + timedelta(hours=2)}
    ]
    
    # Set channel id
    test_project.discord_channel_id = "12345"
    await db.commit() # Relationship fix: db.commit clears session? No, it's ok.
    await db.refresh(test_project)
    
    poll = await service.create_poll(test_project, "Test Poll", "Desc", candidates, test_user.id)
    
    assert poll.title == "Test Poll"
    assert len(poll.candidates) == 1
    assert poll.message_id == "mock_msg_id"
    mock_discord_service.send_channel_message.assert_called_once()

@pytest.mark.asyncio
async def test_poll_upsert_answer(db, test_user):
    poll = SchedulePoll(project_id=uuid4(), title="Test", creator_id=test_user.id)
    db.add(poll)
    await db.flush()
    
    candidate = SchedulePollCandidate(poll_id=poll.id, start_datetime=datetime.now(timezone.utc), end_datetime=datetime.now(timezone.utc))
    db.add(candidate)
    await db.commit()
    
    service = SchedulePollService(db, MagicMock())
    await service.upsert_answer(candidate.id, test_user.id, "ok")
    
    # Check
    from sqlalchemy import select
    res = await db.execute(select(SchedulePollAnswer).where(SchedulePollAnswer.candidate_id == candidate.id))
    answer = res.scalar_one()
    assert answer.status == "ok"
    
    # Update
    await service.upsert_answer(candidate.id, test_user.id, "ng")
    await db.refresh(answer)
    assert answer.status == "ng"
