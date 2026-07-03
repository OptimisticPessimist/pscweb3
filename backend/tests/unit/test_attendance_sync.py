"""稽古と出欠確認イベントの同期ロジックのテスト.

出欠データがWeb上の登録内容とDiscord通知・JSON出力でズレる不具合の回帰テスト:
- 稽古の日時変更が出欠イベントに反映されない
- 参加者/キャスト変更が出欠対象者に反映されない
- 稽古削除後もリマインダーが送信され続ける
- 出欠イベントに rehearsal_id が設定されない
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    AttendanceEvent,
    AttendanceTarget,
    ProjectMember,
    Rehearsal,
    RehearsalParticipant,
    RehearsalSchedule,
    Script,
    TheaterProject,
    User,
)
from src.services.attendance import (
    AttendanceService,
    complete_rehearsal_attendance_events,
    sync_rehearsal_attendance_events,
    to_utc,
)


async def _create_member_user(
    db: AsyncSession,
    project: TheaterProject,
    discord_id: str,
    name: str,
) -> User:
    user = User(discord_id=discord_id, discord_username=name, screen_name=name)
    db.add(user)
    await db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role="editor"))
    return user


async def _create_event(
    db: AsyncSession,
    project: TheaterProject,
    *,
    rehearsal_id: uuid.UUID | None,
    schedule_date: datetime,
    deadline: datetime,
    title: str = "稽古: 07/10 19:00",
) -> AttendanceEvent:
    event = AttendanceEvent(
        project_id=project.id,
        rehearsal_id=rehearsal_id,
        message_id="m1",
        channel_id="c1",
        title=title,
        schedule_date=schedule_date,
        deadline=deadline,
        completed=False,
        reminder_1_sent_at=datetime.now(UTC),
        reminder_2_sent_at=datetime.now(UTC),
    )
    db.add(event)
    await db.flush()
    return event


class TestToUtc:
    def test_naive_is_treated_as_utc(self):
        dt = datetime(2026, 7, 10, 10, 0)
        assert to_utc(dt) == datetime(2026, 7, 10, 10, 0, tzinfo=UTC)

    def test_aware_non_utc_is_converted_not_relabeled(self):
        from datetime import timezone

        jst = timezone(timedelta(hours=9))
        dt = datetime(2026, 7, 10, 19, 0, tzinfo=jst)
        assert to_utc(dt) == datetime(2026, 7, 10, 10, 0, tzinfo=UTC)

    def test_none(self):
        assert to_utc(None) is None


@pytest.mark.asyncio
async def test_sync_updates_schedule_deadline_title_and_resets_reminders(
    db: AsyncSession, test_project: TheaterProject
):
    """日時変更がイベントの日時・期限・タイトルに反映され、リマインダーがリセットされる."""
    rehearsal_id = uuid.uuid4()
    old_date = datetime(2026, 7, 10, 10, 0, tzinfo=UTC)  # JST 07/10 19:00
    deadline = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
    event = await _create_event(
        db,
        test_project,
        rehearsal_id=rehearsal_id,
        schedule_date=old_date,
        deadline=deadline,
        title="稽古: 07/10 19:00 (#1 シーン)",
    )
    await db.commit()

    new_date = datetime(2026, 7, 12, 10, 0, tzinfo=UTC)  # JST 07/12 19:00
    synced = await sync_rehearsal_attendance_events(
        db,
        rehearsal_id=rehearsal_id,
        project_id=test_project.id,
        old_schedule_date=old_date,
        new_schedule_date=new_date,
    )
    await db.commit()

    assert synced == 1
    await db.refresh(event)
    assert to_utc(event.schedule_date) == new_date
    # 期限は日時変更と同じ差分(+2日)だけ移動する
    assert to_utc(event.deadline) == deadline + timedelta(days=2)
    # タイトルの旧日時表記(JST)が新日時に置換される
    assert event.title == "稽古: 07/12 19:00 (#1 シーン)"
    # 新しい日時基準でリマインダーを再送できるようリセットされる
    assert event.reminder_1_sent_at is None
    assert event.reminder_2_sent_at is None
    assert event.reminder_3_sent_at is None


@pytest.mark.asyncio
async def test_sync_adopts_legacy_event_without_rehearsal_id(
    db: AsyncSession, test_project: TheaterProject
):
    """rehearsal_id 未設定の既存イベントも旧日時で照合され、rehearsal_id が補完される."""
    rehearsal_id = uuid.uuid4()
    old_date = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
    event = await _create_event(
        db,
        test_project,
        rehearsal_id=None,
        schedule_date=old_date,
        deadline=old_date - timedelta(days=1),
    )
    await db.commit()

    new_date = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
    synced = await sync_rehearsal_attendance_events(
        db,
        rehearsal_id=rehearsal_id,
        project_id=test_project.id,
        old_schedule_date=old_date,
        new_schedule_date=new_date,
    )
    await db.commit()

    assert synced == 1
    await db.refresh(event)
    assert event.rehearsal_id == rehearsal_id
    assert to_utc(event.schedule_date) == new_date


@pytest.mark.asyncio
async def test_sync_targets_preserves_existing_answers(
    db: AsyncSession, test_project: TheaterProject
):
    """対象者の同期は既存の回答を保持しつつ、追加/削除だけを反映する."""
    rehearsal_id = uuid.uuid4()
    old_date = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    event = await _create_event(
        db,
        test_project,
        rehearsal_id=rehearsal_id,
        schedule_date=old_date,
        deadline=old_date - timedelta(days=1),
    )
    user_a = await _create_member_user(db, test_project, "1001", "member_a")  # 回答済み
    user_b = await _create_member_user(db, test_project, "1002", "member_b")  # 対象から外れる
    user_c = await _create_member_user(db, test_project, "1003", "member_c")  # 新規追加
    await db.flush()
    db.add(AttendanceTarget(event_id=event.id, user_id=user_a.id, status="ok"))
    db.add(AttendanceTarget(event_id=event.id, user_id=user_b.id, status="ng"))
    await db.commit()

    # 存在しないユーザーIDが混ざっても無視される（Userテーブルで検証されるため）
    unknown_user_id = uuid.uuid4()
    synced = await sync_rehearsal_attendance_events(
        db,
        rehearsal_id=rehearsal_id,
        project_id=test_project.id,
        old_schedule_date=old_date,
        new_schedule_date=old_date,
        target_user_ids={user_a.id, user_c.id, unknown_user_id},
    )
    await db.commit()

    assert synced == 1
    result = await db.execute(
        select(AttendanceTarget).where(AttendanceTarget.event_id == event.id)
    )
    targets = {t.user_id: t.status for t in result.scalars().all()}
    # A: 回答が保持される / B: 削除される / C: pendingで追加 / 不明IDは追加されない
    assert targets == {user_a.id: "ok", user_c.id: "pending"}


@pytest.mark.asyncio
async def test_sync_without_date_change_keeps_reminders(
    db: AsyncSession, test_project: TheaterProject
):
    """日時が変わらない場合はリマインダー送信済みフラグを維持する."""
    rehearsal_id = uuid.uuid4()
    date = datetime(2026, 9, 10, 9, 0, tzinfo=UTC)
    event = await _create_event(
        db,
        test_project,
        rehearsal_id=rehearsal_id,
        schedule_date=date,
        deadline=date - timedelta(days=1),
    )
    await db.commit()

    await sync_rehearsal_attendance_events(
        db,
        rehearsal_id=rehearsal_id,
        project_id=test_project.id,
        old_schedule_date=date,
        new_schedule_date=date,
        target_user_ids=set(),
    )
    await db.commit()
    await db.refresh(event)

    assert event.reminder_1_sent_at is not None
    assert event.reminder_2_sent_at is not None


@pytest.mark.asyncio
async def test_complete_rehearsal_attendance_events(
    db: AsyncSession, test_project: TheaterProject
):
    """稽古削除時にイベントが完了扱いになり、リマインダー対象から外れる."""
    rehearsal_id = uuid.uuid4()
    date = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    event = await _create_event(
        db,
        test_project,
        rehearsal_id=rehearsal_id,
        schedule_date=date,
        deadline=date - timedelta(days=1),
    )
    await db.commit()

    completed = await complete_rehearsal_attendance_events(
        db,
        rehearsal_id=rehearsal_id,
        project_id=test_project.id,
        schedule_date=date,
    )
    await db.commit()
    await db.refresh(event)

    assert completed == 1
    assert event.completed is True


@pytest.mark.asyncio
async def test_create_attendance_event_sets_rehearsal_id(
    db: AsyncSession, test_project: TheaterProject
):
    """出欠イベント作成時に rehearsal_id が保存される（フロントの照合キー）."""
    test_project.discord_channel_id = "ch-1"
    user = await _create_member_user(db, test_project, "2001", "member")
    await db.commit()

    discord_service = AsyncMock()
    discord_service.send_channel_message.return_value = {"id": "msg-1"}
    service = AttendanceService(db, discord_service)

    rehearsal_id = uuid.uuid4()
    event = await service.create_attendance_event(
        project=test_project,
        title="稽古: 10/10 19:00",
        deadline=datetime(2026, 10, 9, 10, 0, tzinfo=UTC),
        schedule_date=datetime(2026, 10, 10, 10, 0, tzinfo=UTC),
        target_user_ids=[user.id],
        rehearsal_id=rehearsal_id,
    )

    assert event is not None
    assert event.rehearsal_id == rehearsal_id
    result = await db.execute(
        select(AttendanceTarget).where(AttendanceTarget.event_id == event.id)
    )
    targets = result.scalars().all()
    assert len(targets) == 1
    assert targets[0].status == "pending"


@pytest.mark.asyncio
async def test_update_rehearsal_api_syncs_attendance_event(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    test_user_token: str,
):
    """稽古更新APIが紐づく出欠イベントの日時・対象者を同期する（回帰テスト）."""
    # 稽古スケジュールと稽古を作成
    script = Script(project_id=test_project.id, title="脚本", content="", uploaded_by=test_user.id)
    db.add(script)
    await db.flush()
    schedule = RehearsalSchedule(project_id=test_project.id, script_id=script.id)
    db.add(schedule)
    await db.flush()

    old_date = datetime(2026, 11, 10, 10, 0, tzinfo=UTC)
    rehearsal = Rehearsal(schedule_id=schedule.id, date=old_date, duration_minutes=120)
    db.add(rehearsal)
    await db.flush()
    db.add(
        RehearsalParticipant(rehearsal_id=rehearsal.id, user_id=test_user.id, staff_role=None)
    )

    other_user = await _create_member_user(db, test_project, "3001", "other")

    # 紐づく出欠イベント（test_userのみ対象、回答済み）
    event = await _create_event(
        db,
        test_project,
        rehearsal_id=rehearsal.id,
        schedule_date=old_date,
        deadline=old_date - timedelta(days=1),
    )
    db.add(AttendanceTarget(event_id=event.id, user_id=test_user.id, status="ok"))
    await db.commit()

    # 日時変更 + 参加者に other_user を追加
    new_date = datetime(2026, 11, 12, 10, 0, tzinfo=UTC)
    response = await client.put(
        f"/api/rehearsals/{rehearsal.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "date": new_date.isoformat(),
            "participants": [
                {"user_id": str(test_user.id), "staff_role": None},
                {"user_id": str(other_user.id), "staff_role": "照明"},
            ],
        },
    )
    assert response.status_code == 200, response.text

    await db.refresh(event)
    assert to_utc(event.schedule_date) == new_date
    assert to_utc(event.deadline) == old_date - timedelta(days=1) + timedelta(days=2)
    assert event.reminder_1_sent_at is None

    result = await db.execute(
        select(AttendanceTarget).where(AttendanceTarget.event_id == event.id)
    )
    targets = {t.user_id: t.status for t in result.scalars().all()}
    assert targets == {test_user.id: "ok", other_user.id: "pending"}


@pytest.mark.asyncio
async def test_delete_rehearsal_api_completes_attendance_event(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
    test_user_token: str,
):
    """稽古削除APIが紐づく出欠イベントを完了扱いにする（回帰テスト）."""
    script = Script(project_id=test_project.id, title="脚本", content="", uploaded_by=test_user.id)
    db.add(script)
    await db.flush()
    schedule = RehearsalSchedule(project_id=test_project.id, script_id=script.id)
    db.add(schedule)
    await db.flush()

    date = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)
    rehearsal = Rehearsal(schedule_id=schedule.id, date=date, duration_minutes=120)
    db.add(rehearsal)
    await db.flush()

    event = await _create_event(
        db,
        test_project,
        rehearsal_id=rehearsal.id,
        schedule_date=date,
        deadline=date - timedelta(days=1),
    )
    await db.commit()

    response = await client.delete(
        f"/api/rehearsals/{rehearsal.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200, response.text

    await db.refresh(event)
    assert event.completed is True
