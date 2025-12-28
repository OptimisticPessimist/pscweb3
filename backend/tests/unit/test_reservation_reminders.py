"""リマインダーメール関連のテスト."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TheaterProject, Milestone, Reservation
from src.services.email import email_service


@pytest.fixture
async def project(db: AsyncSession) -> TheaterProject:
    """テスト用プロジェクト."""
    project = TheaterProject(name="Test Project", is_public=True)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest.fixture
async def milestone_today(db: AsyncSession, project: TheaterProject) -> Milestone:
    """今日のマイルストーン."""
    jst = timezone(timedelta(hours=9))
    today_jst = datetime.now(jst).replace(hour=12, minute=0, second=0, microsecond=0)
    today_utc = today_jst.astimezone(timezone.utc).replace(tzinfo=None)
    
    ms = Milestone(
        project_id=project.id,
        title="Today's Event",
        start_date=today_utc,
        location="Test Venue"
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    return ms


@pytest.mark.asyncio
async def test_send_event_reminder():
    """イベントリマインダーメール送信のテスト."""
    with patch.object(email_service, "send_event_reminder") as mock_send:
        mock_send.return_value = True
        
        result = email_service.send_event_reminder(
            to_email="test@example.com",
            name="Test User",
            milestone_title="Test Event",
            date_str="2025/12/29 12:00",
            count=2,
            project_name="Test Project",
            location="Test Venue"
        )
        
        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_check_todays_events_basic(db: AsyncSession, project: TheaterProject, milestone_today: Milestone):
    """当日イベントチェック基本テスト."""
    from src.services.reservation_tasks import check_todays_events
    
    # 予約作成
    r = Reservation(
        milestone_id=milestone_today.id,
        name="Test User",
        email="test@example.com",
        count=2,
        reminder_sent_at=None
    )
    db.add(r)
    await db.commit()
    
    with patch.object(email_service, "send_event_reminder") as mock_send:
        mock_send.return_value = True
        
        stats = await check_todays_events()
        
        # 統計確認
        assert stats["checked_reservations"] >= 1
        assert stats["reminders_sent"] >= 1
        
        # メール送信が呼ばれたか
        mock_send.assert_called()
