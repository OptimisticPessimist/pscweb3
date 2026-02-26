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

@pytest.mark.asyncio
async def test_get_unanswered_members(db, test_project, test_user):
    from src.db.models import ProjectMember, User
    from sqlalchemy import select
    
    # Add a second user
    user2 = User(discord_id="uid2", discord_username="user2")
    db.add(user2)
    await db.flush()
    
    # Add members
    if not (await db.execute(select(ProjectMember).where(ProjectMember.user_id == test_user.id))).scalar_one_or_none():
        db.add(ProjectMember(project_id=test_project.id, user_id=test_user.id, display_name="User1", role="owner"))
    db.add(ProjectMember(project_id=test_project.id, user_id=user2.id, display_name="User2", role="editor"))
    await db.flush()
    
    poll = SchedulePoll(id=uuid4(), project_id=test_project.id, title="Test List", creator_id=test_user.id)
    db.add(poll)
    
    candidate = SchedulePollCandidate(id=uuid4(), poll_id=poll.id, start_datetime=datetime.now(timezone.utc), end_datetime=datetime.now(timezone.utc))
    db.add(candidate)
    await db.flush()
    
    service = SchedulePollService(db, MagicMock())
    
    # No answers yet -> both are unanswered
    unanswered = await service.get_unanswered_members(poll.id)
    assert len(unanswered) == 2
    
    # User1 answers
    await service.upsert_answer(candidate.id, test_user.id, "ok")
    
    # Expire session to ensure relations are refetched
    db.expunge_all()
    
    # Now only User2 is unanswered
    unanswered2 = await service.get_unanswered_members(poll.id)
    assert len(unanswered2) == 1
    assert unanswered2[0]["user_id"] == user2.id

@pytest.mark.asyncio
async def test_send_reminder(db, mock_discord_service, test_project, test_user):
    test_project.discord_channel_id = "12345"
    await db.commit()
    await db.refresh(test_project)
    
    poll = SchedulePoll(id=uuid4(), project_id=test_project.id, title="Reminder Test", creator_id=test_user.id)
    db.add(poll)
    await db.flush()
    
    service = SchedulePollService(db, mock_discord_service)
    
    # test_user has a discord_id set in fixture probably ("user-1234" usually)
    # just test if discord service is called
    await service.send_reminder(poll.id, [test_user.id], "http://localhost")
    
    mock_discord_service.send_channel_message.assert_called_once()
    call_args = mock_discord_service.send_channel_message.call_args[1]
    assert call_args["channel_id"] == "12345"
    assert "Reminder Test" in call_args["content"]
