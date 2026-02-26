"""稽古ICSファイル生成のテスト."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.db.models import User, TheaterProject, RehearsalSchedule, Script, Rehearsal
from src.services.discord import DiscordService

@pytest.mark.asyncio
async def test_update_rehearsal_ics_notification(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """稽古更新時のICS通知テスト."""
    # Arrange: 脚本とスケジュール、稽古を作成
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Test Script",
        content="Test Content"
    )
    db.add(script)
    await db.commit()
    
    schedule = RehearsalSchedule(
        project_id=test_project.id,
        script_id=script.id
    )
    db.add(schedule)
    await db.commit()
    
    from datetime import datetime, timezone, timedelta
    rehearsal = Rehearsal(
        schedule_id=schedule.id,
        date=datetime.now(timezone.utc) + timedelta(days=1),
        duration_minutes=60,
        location="Test Hall"
    )
    db.add(rehearsal)
    await db.commit()
    await db.refresh(rehearsal)

    # test_projectにwebhookを設定
    test_project.discord_webhook_url = "https://discord.com/api/webhooks/test"
    await db.commit()

    update_data = {
        "location": "Updated Hall",
        "notes": "Updated notes"
    }

    # DiscordService.send_notificationをモック
    with patch("src.services.discord.DiscordService.send_notification", new_callable=AsyncMock) as mock_send:
        # Act
        response = await client.put(
            f"/api/rehearsals/{rehearsal.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Assert
        assert response.status_code == 200
        
        # 通知が呼ばれたか確認
        assert mock_send.called
        args, kwargs = mock_send.call_args
        assert "file" in kwargs
        assert kwargs["file"]["filename"] == "rehearsal.ics"
        assert b"BEGIN:VCALENDAR" in kwargs["file"]["content"]
        assert "📌 稽古更新".encode("utf-8") in kwargs["file"]["content"]

@pytest.mark.asyncio
async def test_finalize_poll_ics_notification(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """日程調整確定時のICS通知テスト."""
    # Arrange: 脚本、日程調整、候補日を作成
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Test Script",
        content="Test Content"
    )
    db.add(script)
    await db.commit()

    from src.db.models import SchedulePoll, SchedulePollCandidate
    poll = SchedulePoll(
        project_id=test_project.id,
        title="Test Poll",
        creator_id=test_user.id
    )
    db.add(poll)
    await db.flush()

    from datetime import datetime, timezone, timedelta
    start = datetime.now(timezone.utc) + timedelta(days=2)
    candidate = SchedulePollCandidate(
        poll_id=poll.id,
        start_datetime=start,
        end_datetime=start + timedelta(hours=2)
    )
    db.add(candidate)
    await db.commit()

    # test_projectにwebhookを設定
    test_project.discord_webhook_url = "https://discord.com/api/webhooks/test"
    await db.commit()

    finalize_data = {
        "candidate_id": str(candidate.id),
        "scene_ids": []
    }

    # DiscordService.send_notificationをモック
    with patch("src.services.discord.DiscordService.send_notification", new_callable=AsyncMock) as mock_send:
        # Act
        response = await client.post(
            f"/api/projects/{test_project.id}/polls/{poll.id}/finalize",
            json=finalize_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Assert
        assert response.status_code == 200
        
        # 通知が呼ばれたか確認
        assert mock_send.called
        args, kwargs = mock_send.call_args
        assert "file" in kwargs
        assert kwargs["file"]["filename"] == "rehearsal.ics"
        assert b"BEGIN:VCALENDAR" in kwargs["file"]["content"]
        assert "📌 稽古確定".encode("utf-8") in kwargs["file"]["content"]
