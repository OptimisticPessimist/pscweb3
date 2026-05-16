import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.db.models import AttendanceEvent, AttendanceTarget, TheaterProject, User
from src.services.attendance_tasks import check_deadlines


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
    assert stats["schedule_reminders_sent"] == 0
    assert stats["deadline_reminders_sent"] == 0
    assert stats["errors"] == 0
    mock_discord_service.send_channel_message.assert_not_called()


@pytest.mark.asyncio
async def test_check_deadlines_send_reminder(mock_db_session, mock_discord_service):
    """リマインダーを送信するテスト."""
    # テストデータ準備
    project_id = uuid.uuid4()
    event_id = uuid.uuid4()
    user_id = uuid.uuid4()

    project = TheaterProject(
        id=project_id,
        discord_channel_id="123456789",
        attendance_reminder_1_hours=48,
        attendance_reminder_2_hours=24,
        attendance_reminder_3_hours=12,
    )
    user = User(id=user_id, discord_id="987654321")

    target = AttendanceTarget(user_id=user_id, status="pending", user=user)

    event = AttendanceEvent(
        id=event_id,
        title="Test Event",
        schedule_date=datetime.now(UTC) + timedelta(hours=10),
        deadline=datetime.now(UTC) + timedelta(hours=5),
        reminder_1_sent_at=None,
        reminder_2_sent_at=None,
        reminder_3_sent_at=None,
        completed=False,
        project=project,
        targets=[target],
    )

    # DB戻り値設定
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    # 検証
    assert stats["checked_events"] == 1
    assert stats["schedule_reminders_sent"] == 1
    assert stats["errors"] == 0

    # Discord送信確認
    mock_discord_service.send_channel_message.assert_called_once()
    call_args = mock_discord_service.send_channel_message.call_args[1]
    assert call_args["channel_id"] == "123456789"
    assert "<@987654321>" in call_args["content"]

    # DB更新確認 (reminder_1_sent_atが設定されたか)
    assert event.reminder_1_sent_at is not None
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_deadlines_no_pending_users(mock_db_session, mock_discord_service):
    """未回答ユーザーがいない場合のテスト (リマインダー送信しない)."""
    # テストデータ準備
    project_id = uuid.uuid4()
    event = AttendanceEvent(
        id=uuid.uuid4(),
        title="Test Event",
        schedule_date=datetime.now(UTC) + timedelta(hours=20),
        deadline=datetime.now(UTC) - timedelta(hours=1),
        reminder_1_sent_at=None,
        reminder_2_sent_at=None,
        reminder_3_sent_at=None,
        completed=False,
        project=TheaterProject(
            id=project_id,
            discord_channel_id="123456789",
            attendance_reminder_1_hours=48,
            attendance_reminder_2_hours=24,
            attendance_reminder_3_hours=12,
        ),
        targets=[
            AttendanceTarget(status="ok", user=User(discord_id="111")),  # OKなので対象外
            AttendanceTarget(status="ng", user=User(discord_id="222")),  # NGなので対象外
        ],
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    assert stats["checked_events"] == 1
    assert stats["schedule_reminders_sent"] == 0  # 送信数0
    assert stats["deadline_reminders_sent"] == 0
    assert stats["errors"] == 0

    mock_discord_service.send_channel_message.assert_not_called()

    # 送信はしていないが、対象者がいない場合は送信済み扱いになる
    assert event.reminder_1_sent_at is not None
    assert event.reminder_2_sent_at is not None
    assert event.reminder_3_sent_at is None
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_deadlines_no_discord_channel(mock_db_session, mock_discord_service):
    """DiscordチャンネルID設定なしの場合."""
    event = AttendanceEvent(
        id=uuid.uuid4(),
        title="Test Event",
        schedule_date=datetime.now(UTC) + timedelta(hours=10),
        deadline=datetime.now(UTC) - timedelta(minutes=10),
        reminder_1_sent_at=None,
        reminder_2_sent_at=None,
        reminder_3_sent_at=None,
        completed=False,
        project=TheaterProject(
            id=uuid.uuid4(),
            name="Test Project",
            discord_channel_id=None,
            attendance_reminder_1_hours=48,
            attendance_reminder_2_hours=24,
            attendance_reminder_3_hours=12,
        ),  # IDなし
        targets=[AttendanceTarget(status="pending", user=User(discord_id="123"))],
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
    assert stats["schedule_reminders_sent"] == 0
    assert stats["deadline_reminders_sent"] == 0
    assert stats["errors"] == 0

    mock_discord_service.send_channel_message.assert_not_called()

    # reminder_sent_atは更新される (return直前に更新ロジックがない場合更新されない？)
    # 実装確認: reminder_sent_at = now は await _send_reminder 呼び出しの後。
    # _send_reminder内で早期リターンの場合...
    # 実装:
    #   await _send_reminder(...)
    #   event.reminder_sent_at = now
    # なので、更新されるはず。
    assert event.reminder_1_sent_at is not None


@pytest.mark.asyncio
async def test_check_deadlines_send_reminder_3(mock_db_session, mock_discord_service):
    """3回目のリマインダーを送信するテスト."""
    project_id = uuid.uuid4()
    
    # 1回目、2回目は送信済みとする
    now = datetime.now(UTC)
    event = AttendanceEvent(
        id=uuid.uuid4(),
        title="Test Event 3rd Reminder",
        schedule_date=now + timedelta(hours=10),  # 12時間前を切っている
        deadline=now + timedelta(hours=5),
        reminder_1_sent_at=now - timedelta(days=2),
        reminder_2_sent_at=now - timedelta(days=1),
        reminder_3_sent_at=None,
        completed=False,
        project=TheaterProject(
            id=project_id,
            discord_channel_id="123456789",
            attendance_reminder_1_hours=48,
            attendance_reminder_2_hours=24,
            attendance_reminder_3_hours=12,
        ),
        targets=[
            # OKのユーザー：送信対象
            AttendanceTarget(status="ok", user=User(discord_id="user_ok")),
            # NGのユーザー：送信対象外
            AttendanceTarget(status="ng", user=User(discord_id="user_ng")),
            # 未回答のユーザー：送信対象
            AttendanceTarget(status="pending", user=User(discord_id="user_pending")),
        ],
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    assert stats["checked_events"] == 1
    assert stats["schedule_reminders_sent"] == 1
    
    # Discord送信確認
    mock_discord_service.send_channel_message.assert_called_once()
    call_args = mock_discord_service.send_channel_message.call_args[1]
    msg = call_args["content"]
    assert "<@user_ok>" in msg
    assert "<@user_pending>" in msg
    assert "<@user_ng>" not in msg
    
    # 12時間前の独自メッセージが含まれるか
    assert "間もなく稽古(12時間前)です" in msg

    assert event.reminder_3_sent_at is not None
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_deadlines_skip_past_events(mock_db_session, mock_discord_service):
    """過去の稽古に対してリマインダーを送信しないテスト."""
    now = datetime.now(UTC)

    # schedule_date が過去のイベント
    event = AttendanceEvent(
        id=uuid.uuid4(),
        title="Past Event",
        schedule_date=now - timedelta(days=3),  # 3日前の稽古
        deadline=now - timedelta(days=4),
        reminder_1_sent_at=None,
        reminder_2_sent_at=None,
        reminder_3_sent_at=None,
        completed=False,
        project=TheaterProject(
            id=uuid.uuid4(),
            discord_channel_id="123456789",
            attendance_reminder_1_hours=48,
            attendance_reminder_2_hours=24,
            attendance_reminder_3_hours=12,
        ),
        targets=[
            AttendanceTarget(status="pending", user=User(discord_id="user1")),
        ],
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [event]
    mock_db_session.execute.return_value = mock_result

    stats = await check_deadlines()

    # 通知は送信されない
    assert stats["checked_events"] == 1
    assert stats["past_events_skipped"] == 1
    assert stats["schedule_reminders_sent"] == 0
    assert stats["deadline_reminders_sent"] == 0
    mock_discord_service.send_channel_message.assert_not_called()

    # リマインダーは全て「送信済み」マークされる（再度拾われない）
    assert event.reminder_1_sent_at is not None
    assert event.reminder_2_sent_at is not None
    assert event.reminder_3_sent_at is not None
    mock_db_session.commit.assert_awaited_once()
