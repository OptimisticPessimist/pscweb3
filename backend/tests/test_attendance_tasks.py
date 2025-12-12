import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.attendance_tasks import check_deadlines
from src.db.models import AttendanceEvent, AttendanceTarget, TheaterProject, User

@pytest.fixture
def mock_db_session():
    """DBセッションのモック."""
    with patch("src.services.attendance_tasks.async_session_maker") as mock_factory:
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_discord_service():
    """Discordサービスのモック."""
    with patch("src.services.attendance_tasks.get_discord_service") as mock_get:
        mock_service = AsyncMock()
        mock_get.return_value = mock_service
        yield mock_service

@pytest.mark.asyncio
async def test_check_deadlines_no_events(mock_db_session, mock_discord_service):
    """期限切れイベントがない場合のテスト."""
    # DB戻り値設定: イベントなし
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    assert stats["checked_events"] == 0
    assert stats["reminders_sent"] == 0
    assert stats["errors"] == 0
    mock_discord_service.send_channel_message.assert_not_called()

@pytest.mark.asyncio
async def test_check_deadlines_send_reminder(mock_db_session, mock_discord_service):
    """リマインダーを送信するテスト."""
    # テストデータ準備
    project_id = uuid.uuid4()
    event_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    project = TheaterProject(id=project_id, discord_channel_id="123456789")
    user = User(id=user_id, discord_id="987654321")
    
    target = AttendanceTarget(user_id=user_id, status="pending", user=user)
    
    event = AttendanceEvent(
        id=event_id,
        title="Test Event",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1), # 1時間前に期限切れ
        reminder_sent_at=None,
        completed=False,
        project=project,
        targets=[target]
    )

    # DB戻り値設定
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    # 検証
    assert stats["checked_events"] == 1
    assert stats["reminders_sent"] == 1
    assert stats["errors"] == 0
    
    # Discord送信確認
    mock_discord_service.send_channel_message.assert_called_once()
    call_args = mock_discord_service.send_channel_message.call_args[1]
    assert call_args["channel_id"] == "123456789"
    assert "<@987654321>" in call_args["content"]
    
    # DB更新確認 (reminder_sent_atが設定されたか)
    assert event.reminder_sent_at is not None
    mock_db_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_check_deadlines_no_pending_users(mock_db_session, mock_discord_service):
    """未回答ユーザーがいない場合のテスト (リマインダー送信しない)."""
    # テストデータ準備
    project_id = uuid.uuid4()
    event = AttendanceEvent(
        id=uuid.uuid4(),
        title="Test Event",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        reminder_sent_at=None,
        completed=False,
        project=TheaterProject(id=project_id, discord_channel_id="123456789"),
        targets=[
            AttendanceTarget(status="ok", user=User(discord_id="111")), # OKなので対象外
            AttendanceTarget(status="ng", user=User(discord_id="222"))  # NGなので対象外
        ]
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    assert stats["checked_events"] == 1
    assert stats["reminders_sent"] == 0 # 送信数0
    assert stats["errors"] == 0
    
    mock_discord_service.send_channel_message.assert_not_called()
    
    # 送信はしていないが、reminder_sent_atは更新される仕様 (次回以降チェックしないため)
    assert event.reminder_sent_at is not None
    mock_db_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_check_deadlines_no_discord_channel(mock_db_session, mock_discord_service):
    """DiscordチャンネルID設定なしの場合."""
    event = AttendanceEvent(
        id=uuid.uuid4(),
        title="Test Event",
        deadline=datetime.now(timezone.utc) - timedelta(minutes=10),
        reminder_sent_at=None,
        completed=False,
        project=TheaterProject(id=uuid.uuid4(), name="Test Project", discord_channel_id=None), # IDなし
        targets=[AttendanceTarget(status="pending", user=User(discord_id="123"))]
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()
    
    # エラーではなく、単に送信されない (ログ出力はされる)
    # stats上はreminders_sent=0で、エラーカウントもしない実装になっているか確認
    # 実装を見ると: 
    #   if not project.discord_channel_id: return
    #   stats["reminders_sent"] += 1 は呼ばれない
    #   errorsインクリメントもされない (Exceptionではないため)
    
    assert stats["checked_events"] == 1
    assert stats["reminders_sent"] == 0
    assert stats["errors"] == 0
    
    mock_discord_service.send_channel_message.assert_not_called()
    
    # reminder_sent_atは更新される (return直前に更新ロジックがない場合更新されない？)
    # 実装確認: reminder_sent_at = now は await _send_reminder 呼び出しの後。
    # _send_reminder内で早期リターンの場合...
    # 実装: 
    #   await _send_reminder(...)
    #   event.reminder_sent_at = now
    # なので、更新されるはず。
    assert event.reminder_sent_at is not None
