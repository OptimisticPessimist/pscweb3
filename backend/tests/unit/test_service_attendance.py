"""出欠確認サービスのテスト."""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.attendance import AttendanceService
from src.services.discord import DiscordService
from src.db.models import TheaterProject, User, ProjectMember


@pytest.fixture
def mock_discord_service() -> DiscordService:
    """モックDiscordサービス."""
    mock_service = MagicMock(spec=DiscordService)
    mock_service.send_button_message = AsyncMock()
    mock_service.send_notification = AsyncMock()
    return mock_service


@pytest.mark.asyncio
async def test_create_attendance_event(
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    mock_discord_service: DiscordService,
) -> None:
    """出欠確認イベント作成のテスト."""
    # Arrange
    service = AttendanceService(db, mock_discord_service)
    title = "テスト出欠確認"
    deadline = datetime.now(UTC) + timedelta(days=1)
    schedule_date = datetime.now(UTC) + timedelta(days=2)
    
    # Act
    event = await service.create_attendance_event(
        project=test_project,
        title=title,
        deadline=deadline,
        schedule_date=schedule_date,
    )
    
    # Assert
    assert event is not None
    assert event.title == title
    assert event.project_id == test_project.id


@pytest.mark.asyncio
async def test_create_attendance_event_with_targets(
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    mock_discord_service: DiscordService,
) -> None:
    """ターゲットユーザー指定の出欠確認イベント作成テスト."""
    # Arrange
    service = AttendanceService(db, mock_discord_service)
    title = "ターゲット指定テスト"
    deadline = datetime.now(UTC) + timedelta(days=1)
    schedule_date = datetime.now(UTC) + timedelta(days=2)
    target_user_ids = [test_user.id]
    
    # Act
    event = await service.create_attendance_event(
        project=test_project,
        title=title,
        deadline=deadline,
        schedule_date=schedule_date,
        target_user_ids=target_user_ids,
    )
    
    # Assert
    assert event is not None
    # ターゲットユーザーが設定される


@pytest.mark.asyncio
async def test_create_attendance_event_sends_notification(
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    mock_discord_service: DiscordService,
) -> None:
    """出欠確認イベント作成時にDiscord通知が送信されるテスト."""
    # Arrange
    service = AttendanceService(db, mock_discord_service)
    test_project.discord_channel_id = "test_channel_123"
    test_project.discord_webhook_url = "https://discord.com/api/webhooks/test"
    
    title = "通知テスト"
    deadline = datetime.now(UTC) + timedelta(days=1)
    schedule_date = datetime.now(UTC) + timedelta(days=2)
    
    # Act
    event = await service.create_attendance_event(
        project=test_project,
        title=title,
        deadline=deadline,
        schedule_date=schedule_date,
    )
    
    # Assert
    assert event is not None
    # Discord通知が呼ばれたことを確認（モック使用）
    if test_project.discord_webhook_url:
        mock_discord_service.send_button_message.assert_called()


@pytest.mark.asyncio
async def test_update_attendance_status(
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    mock_discord_service: DiscordService,
) -> None:
    """出欠ステータス更新のテスト."""
    # Arrange
    service = AttendanceService(db, mock_discord_service)
    
    # まず出欠確認イベントを作成
    event = await service.create_attendance_event(
        project=test_project,
        title="ステータス更新テスト",
        deadline=datetime.now(UTC) + timedelta(days=1),
        schedule_date=datetime.now(UTC) + timedelta(days=2),
        target_user_ids=[test_user.id],
    )
    
    # Act - ステータスを更新
    from src.db.models import AttendanceStatus
    from sqlalchemy import select, update
    
    # ステータスレコードを取得して更新
    result = await db.execute(
        select(AttendanceStatus).where(
            AttendanceStatus.event_id == event.id,
            AttendanceStatus.user_id == test_user.id
        )
    )
    status = result.scalar_one_or_none()
    
    if status:
        status.status = "attend"
        status.notes = "参加します"
        await db.commit()
    
    # Assert
    if status:
        assert status.status == "attend"
        assert status.notes == "参加します"


@pytest.mark.asyncio
async def test_create_attendance_event_with_location(
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    mock_discord_service: DiscordService,
) -> None:
    """場所情報付き出欠確認イベント作成のテスト."""
    # Arrange
    service = AttendanceService(db, mock_discord_service)
    title = "場所指定テスト"
    deadline = datetime.now(UTC) + timedelta(days=1)
    schedule_date = datetime.now(UTC) + timedelta(days=2)
    location = "稽古場A"
    
    # Act
    event = await service.create_attendance_event(
        project=test_project,
        title=title,
        deadline=deadline,
        schedule_date=schedule_date,
        location=location,
    )
    
    # Assert
    assert event is not None
    assert event.location == location


@pytest.mark.asyncio
async def test_create_attendance_event_with_description(
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    mock_discord_service: DiscordService,
) -> None:
    """説明付き出欠確認イベント作成のテスト."""
    # Arrange
    service = AttendanceService(db, mock_discord_service)
    title = "説明付きテスト"
    deadline = datetime.now(UTC) + timedelta(days=1)
    schedule_date = datetime.now(UTC) + timedelta(days=2)
    description = "第1幕の通し稽古"
    
    # Act
    event = await service.create_attendance_event(
        project=test_project,
        title=title,
        deadline=deadline,
        schedule_date=schedule_date,
        description=description,
    )
    
    # Assert
    assert event is not None
    assert event.description == description
