"""出席確認APIエンドポイント."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog import get_logger

from src.db import get_db
from src.db.models import AttendanceEvent, AttendanceTarget, ProjectMember
from src.dependencies.permissions import check_role, get_project_member_dep
from src.schemas.attendance import (
    AttendanceEventDetailResponse,
    AttendanceEventResponse,
    AttendanceExportResponse,
    AttendanceExportTarget,
    AttendanceStats,
    AttendanceStatusUpdate,
    AttendanceTargetResponse,
    AttendanceTargetUpdate,
)

router = APIRouter()
logger = get_logger(__name__)
JST = timezone(timedelta(hours=9))
ATTENDANCE_EXPORT_SOURCE = "PSCWEB3"
ATTENDANCE_EXPORT_STATUS_LABELS = {
    "ok": "出席",
    "ng": "欠席",
    "pending": "未回答",
}
# 想定外のステータスを「未回答」に黙って丸めると外部アプリ側で誤解されるため、
# 区別可能なラベルを用い、警告ログを残す。
ATTENDANCE_EXPORT_UNKNOWN_STATUS_LABEL = "不明"


def resolve_export_status_label(status: str, *, event_id: UUID, user_id: UUID) -> str:
    """出欠ステータスを外部出力用ラベルに変換する.

    未知のステータスは「未回答」に丸めず、区別可能なラベルにして警告を残す。
    """
    label = ATTENDANCE_EXPORT_STATUS_LABELS.get(status)
    if label is None:
        logger.warning(
            "attendance_export_unknown_status",
            status=status,
            event_id=str(event_id),
            user_id=str(user_id),
        )
        return ATTENDANCE_EXPORT_UNKNOWN_STATUS_LABEL
    return label


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime has UTC timezone.

    Args:
        dt: Datetime object to convert

    Returns:
        Datetime with UTC timezone, or None if input is None
    """
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def ensure_jst(dt: datetime | None) -> datetime | None:
    """Ensure datetime has JST timezone."""
    if dt is None:
        return None
    dt_utc = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt_utc.astimezone(JST)


def build_attendance_export_filename(event: AttendanceEvent) -> str:
    """Build a stable JSON export filename."""
    base_dt = ensure_jst(event.schedule_date or event.created_at)
    if base_dt:
        date_part = base_dt.strftime("%Y%m%d-%H%M")
    else:
        date_part = datetime.now(JST).strftime("%Y%m%d-%H%M")
    return f"attendance-{date_part}-{event.id}.json"


async def build_attendance_export_response(
    project_id: UUID,
    event_id: UUID,
    db: AsyncSession,
) -> tuple[AttendanceEvent, AttendanceExportResponse]:
    """Build external attendance JSON export payload."""
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets).options(selectinload(AttendanceTarget.user)))
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Attendance event not found")

    member_stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
    member_result = await db.execute(member_stmt)
    members = member_result.scalars().all()
    display_name_map = {m.user_id: m.display_name for m in members}

    attendances = []
    for target in sorted(
        event.targets,
        key=lambda t: display_name_map.get(t.user_id) or t.user.display_name,
    ):
        attendances.append(
            AttendanceExportTarget(
                name=display_name_map.get(target.user_id) or target.user.display_name,
                status=resolve_export_status_label(
                    target.status, event_id=event.id, user_id=target.user_id
                ),
            )
        )

    return event, AttendanceExportResponse(
        schemaVersion=1,
        source=ATTENDANCE_EXPORT_SOURCE,
        eventName=event.title,
        generatedAt=datetime.now(JST).replace(microsecond=0).isoformat(),
        attendances=attendances,
    )


@router.get(
    "/{project_id}/attendance/{event_id}/export",
    response_model=AttendanceExportResponse,
)
async def export_attendance_event(
    project_id: UUID,
    event_id: UUID,
    _current_member: ProjectMember = Depends(check_role(["owner", "editor"])),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """出席確認イベントを外部連携用JSONとして出力."""
    event, payload = await build_attendance_export_response(project_id, event_id, db)
    filename = build_attendance_export_filename(event)

    return JSONResponse(
        content=payload.model_dump(mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/attendance/{event_id}", response_model=AttendanceEventDetailResponse)
async def get_attendance_event(
    project_id: UUID,
    event_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> AttendanceEventDetailResponse:
    """出席確認イベントの詳細を取得."""
    # イベント取得
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets).options(selectinload(AttendanceTarget.user)))
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Attendance event not found")

    # ユーザー表示名マップ作成
    member_stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
    member_result = await db.execute(member_stmt)
    members = member_result.scalars().all()
    display_name_map = {m.user_id: m.display_name for m in members}

    # ターゲットリスト作成
    targets_response = []
    for target in event.targets:
        targets_response.append(
            AttendanceTargetResponse(
                user_id=target.user_id,
                display_name=display_name_map.get(target.user_id),
                discord_username=target.user.display_name,
                status=target.status,
            )
        )

    # 集計
    ok_count = sum(1 for t in event.targets if t.status == "ok")
    ng_count = sum(1 for t in event.targets if t.status == "ng")
    pending_count = sum(1 for t in event.targets if t.status == "pending")
    total_count = len(event.targets)

    stats = AttendanceStats(ok=ok_count, ng=ng_count, pending=pending_count, total=total_count)

    # 日時UTC化
    return AttendanceEventDetailResponse(
        id=event.id,
        project_id=event.project_id,
        rehearsal_id=event.rehearsal_id,
        title=event.title,
        schedule_date=ensure_utc(event.schedule_date),
        deadline=ensure_utc(event.deadline),
        completed=event.completed,
        created_at=ensure_utc(event.created_at),
        stats=stats,
        targets=targets_response,
    )


@router.patch(
    "/{project_id}/attendance/{event_id}/targets", response_model=AttendanceEventDetailResponse
)
async def update_attendance_targets(
    project_id: UUID,
    event_id: UUID,
    payload: AttendanceTargetUpdate,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> AttendanceEventDetailResponse:
    """出席確認イベントの対象メンバーを更新."""
    # 権限チェック (Owner/Editor only?)
    if current_member.role == "viewer":
        raise HTTPException(status_code=403, detail="Permission denied")

    # イベント取得
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets))
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Attendance event not found")

    # 削除処理
    if payload.remove_user_ids:
        # 文字列IDをUUIDに変換
        remove_uuids = []
        for uid in payload.remove_user_ids:
            try:
                remove_uuids.append(UUID(uid))
            except ValueError:
                pass

        targets_to_remove = [t for t in event.targets if t.user_id in remove_uuids]
        for t in targets_to_remove:
            await db.delete(t)

    # 追加処理
    if payload.add_user_ids:
        # 既存ターゲットID
        existing_target_ids = {t.user_id for t in event.targets}

        for uid in payload.add_user_ids:
            try:
                user_uuid = UUID(uid)
                if user_uuid not in existing_target_ids:
                    # ユーザー存在確認は省略（外部キー制約任せ）または別途行う
                    new_target = AttendanceTarget(
                        event_id=event.id, user_id=user_uuid, status="pending"
                    )
                    db.add(new_target)
            except ValueError:
                pass

    await db.commit()

    # 再取得して返す
    return await get_attendance_event(project_id, event_id, current_member, db)


@router.get("/{project_id}/attendance", response_model=list[AttendanceEventResponse])
async def list_attendance_events(
    project_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceEventResponse]:
    """出席確認イベント一覧を取得."""
    # イベントとターゲットを取得
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.project_id == project_id)
        .order_by(AttendanceEvent.created_at.desc())
        .options(selectinload(AttendanceEvent.targets))
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    response = []
    for event in events:
        # 集計
        # 現状は同期処理がないため、全てpendingになる可能性がありますが、
        # 将来的に同期処理が入った場合に対応できるように集計します。
        ok_count = sum(1 for t in event.targets if t.status == "ok")
        ng_count = sum(1 for t in event.targets if t.status == "ng")
        pending_count = sum(1 for t in event.targets if t.status == "pending")
        total_count = len(event.targets)

        stats = AttendanceStats(ok=ok_count, ng=ng_count, pending=pending_count, total=total_count)

        # 日時をUTCとしてマーク
        response.append(
            AttendanceEventResponse(
                id=event.id,
                project_id=event.project_id,
                rehearsal_id=event.rehearsal_id,
                title=event.title,
                schedule_date=ensure_utc(event.schedule_date),
                deadline=ensure_utc(event.deadline),
                completed=event.completed,
                created_at=ensure_utc(event.created_at),
                stats=stats,
            )
        )

    return response


@router.post("/{project_id}/attendance/{event_id}/remind-pending")
async def remind_pending_users(
    project_id: UUID,
    event_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Pendingユーザーにリマインダーを送信."""
    from src.db.models import TheaterProject, User
    from src.services.discord import get_discord_service

    # 権限チェック
    if current_member.role == "viewer":
        raise HTTPException(status_code=403, detail="Permission denied")

    # イベント取得
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets).selectinload(AttendanceTarget.user))
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Attendance event not found")

    # Pendingユーザーを抽出
    pending_targets = [t for t in event.targets if t.status == "pending"]

    if not pending_targets:
        return {"message": "No pending users to remind"}

    # Pendingユーザーのdiscord_idを取得
    pending_user_ids = [t.user_id for t in pending_targets]
    user_stmt = select(User).where(User.id.in_(pending_user_ids), User.discord_id.isnot(None))
    user_result = await db.execute(user_stmt)
    pending_users = user_result.scalars().all()

    if not pending_users:
        return {"message": "No pending users with Discord accounts"}

    # プロジェクト取得
    project = await db.get(TheaterProject, project_id)
    if not project or not project.discord_channel_id:
        raise HTTPException(status_code=400, detail="Discord channel not configured")

    # メンション作成
    mentions = [f"<@{u.discord_id}>" for u in pending_users]

    # メッセージ作成
    deadline_str = f"<t:{int(ensure_utc(event.deadline).timestamp())}:f>" if event.deadline else "未設定"
    schedule_str = f"<t:{int(ensure_utc(event.schedule_date).timestamp())}:f>" if event.schedule_date else "未定"

    message_content = (
        f"**【出欠確認リマインダー】{event.title}**\n"
        f"日時: {schedule_str}\n"
        f"期限: {deadline_str}\n"
        f"未回答の方: {' '.join(mentions)}\n\n"
        f"まだ出欠の回答をされていない方は、元のメッセージのボタンから回答をお願いします。"
    )

    # Discord送信
    discord_service = get_discord_service()
    discord_resp = await discord_service.send_channel_message(
        channel_id=project.discord_channel_id,
        content=message_content,
    )

    if not discord_resp:
        raise HTTPException(status_code=500, detail="Failed to send Discord message")

    return {"message": f"Reminder sent to {len(pending_users)} pending users"}


@router.patch(
    "/{project_id}/attendance/{event_id}/my-status", response_model=AttendanceEventDetailResponse
)
async def update_my_attendance_status(
    project_id: UUID,
    event_id: UUID,
    payload: AttendanceStatusUpdate,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> AttendanceEventDetailResponse:
    """自分の出席確認ステータスを更新."""
    # イベント存在確認
    stmt = select(AttendanceEvent).where(
        AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Attendance event not found")

    # 自分のターゲットレコード取得
    target_stmt = select(AttendanceTarget).where(
        AttendanceTarget.event_id == event_id, AttendanceTarget.user_id == current_member.user_id
    )
    target_result = await db.execute(target_stmt)
    target = target_result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="You are not a target of this attendance event")

    # ステータス更新
    if payload.status not in ["ok", "ng", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status value")

    target.status = payload.status
    await db.commit()

    # 更新後の詳細を返す
    return await get_attendance_event(project_id, event_id, current_member, db)
