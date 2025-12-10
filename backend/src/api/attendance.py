"""出席確認APIエンドポイント."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import AttendanceEvent, AttendanceTarget, ProjectMember
from src.dependencies.permissions import get_project_member_dep
from src.schemas.attendance import (
    AttendanceEventDetailResponse,
    AttendanceEventResponse,
    AttendanceStats,
    AttendanceStatusUpdate,
    AttendanceTargetResponse,
    AttendanceTargetUpdate,
)

router = APIRouter()


def ensure_utc(dt: datetime | None) -> datetime | None:
    """日時オブジェクトがUTCタイムゾーンを持つことを保証する.
    
    Args:
        dt: 変換対象の日時オブジェクト
        
    Returns:
        UTCタイムゾーン付きの日時、またはNone（入力がNoneの場合）
    """
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


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
        .options(
            selectinload(AttendanceEvent.targets).options(
                selectinload(AttendanceTarget.user)
            )
        )
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="出席確認イベントが見つかりません")

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
                discord_username=target.user.discord_username,
                status=target.status
            )
        )

    # 集計
    ok_count = sum(1 for t in event.targets if t.status == "ok")
    ng_count = sum(1 for t in event.targets if t.status == "ng")
    pending_count = sum(1 for t in event.targets if t.status == "pending")
    total_count = len(event.targets)

    stats = AttendanceStats(
        ok=ok_count,
        ng=ng_count,
        pending=pending_count,
        total=total_count
    )

    # 日時UTC化
    return AttendanceEventDetailResponse(
        id=event.id,
        project_id=event.project_id,
        title=event.title,
        schedule_date=ensure_utc(event.schedule_date),
        deadline=ensure_utc(event.deadline),
        completed=event.completed,
        created_at=ensure_utc(event.created_at),
        stats=stats,
        targets=targets_response
    )


@router.patch("/{project_id}/attendance/{event_id}/targets", response_model=AttendanceEventDetailResponse)
async def update_attendance_targets(
    project_id: UUID,
    event_id: UUID,
    payload: AttendanceTargetUpdate,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> AttendanceEventDetailResponse:
    """出席確認イベントの対象メンバーを更新."""
    # 権限チェック (Owner/Editor のみ)
    if current_member.role == "viewer":
         raise HTTPException(status_code=403, detail="権限がありません")

    # イベント取得
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets))
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="出席確認イベントが見つかりません")

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
                        event_id=event.id,
                        user_id=user_uuid,
                        status="pending"
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

        stats = AttendanceStats(
            ok=ok_count,
            ng=ng_count,
            pending=pending_count,
            total=total_count
        )

        # 日時をUTCとしてマーク
        response.append(
            AttendanceEventResponse(
                id=event.id,
                project_id=event.project_id,
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
        raise HTTPException(status_code=403, detail="権限がありません")

    # イベント取得
    stmt = (
        select(AttendanceEvent)
        .where(AttendanceEvent.id == event_id, AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets).selectinload(AttendanceTarget.user))
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="出席確認イベントが見つかりません")

    # Pendingユーザーを抽出
    pending_targets = [t for t in event.targets if t.status == "pending"]

    if not pending_targets:
        return {"message": "リマインダーを送信する未回答ユーザーがいません"}

    # Pendingユーザーのdiscord_idを取得
    pending_user_ids = [t.user_id for t in pending_targets]
    user_stmt = select(User).where(User.id.in_(pending_user_ids), User.discord_id.isnot(None))
    user_result = await db.execute(user_stmt)
    pending_users = user_result.scalars().all()

    if not pending_users:
        return {"message": "Discordアカウントを持つ未回答ユーザーがいません"}

    # プロジェクト取得
    project = await db.get(TheaterProject, project_id)
    if not project or not project.discord_channel_id:
        raise HTTPException(status_code=400, detail="Discordチャンネルが設定されていません")

    # メンション作成
    mentions = [f"<@{u.discord_id}>" for u in pending_users]

    # メッセージ作成
    deadline_str = event.deadline.strftime('%Y-%m-%d %H:%M') if event.deadline else "未設定"
    schedule_str = event.schedule_date.strftime('%Y-%m-%d %H:%M') if event.schedule_date else "未定"

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
        raise HTTPException(status_code=500, detail="Discordメッセージの送信に失敗しました")

    return {"message": f"{len(pending_users)}名の未回答ユーザーにリマインダーを送信しました"}


@router.patch("/{project_id}/attendance/{event_id}/my-status", response_model=AttendanceEventDetailResponse)
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
        AttendanceEvent.id == event_id,
        AttendanceEvent.project_id == project_id
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="出席確認イベントが見つかりません")

    # 自分のターゲットレコード取得
    target_stmt = select(AttendanceTarget).where(
        AttendanceTarget.event_id == event_id,
        AttendanceTarget.user_id == current_member.user_id
    )
    target_result = await db.execute(target_stmt)
    target = target_result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="この出席確認イベントの対象ではありません")

    # ステータス更新
    if payload.status not in ["ok", "ng", "pending"]:
        raise HTTPException(status_code=400, detail="無効なステータス値です")

    target.status = payload.status
    await db.commit()

    # 更新後の詳細を返す
    return await get_attendance_event(project_id, event_id, current_member, db)

