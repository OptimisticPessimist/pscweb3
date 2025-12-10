"""出席確認APIエンドポイント."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import AttendanceEvent, AttendanceTarget
from src.dependencies.permissions import get_project_member_dep
from src.db.models import ProjectMember
from src.schemas.attendance import (
    AttendanceEventResponse, 
    AttendanceStats, 
    AttendanceEventDetailResponse, 
    AttendanceTargetResponse,
    AttendanceTargetUpdate
)

router = APIRouter()


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime has UTC timezone.
    
    Args:
        dt: Datetime object to convert
        
    Returns:
        Datetime with UTC timezone, or None if input is None
    """
    from datetime import timezone
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


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
    from src.services.discord import get_discord_service
    from src.db.models import User, TheaterProject
    
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
    from datetime import timezone
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
        raise HTTPException(status_code=500, detail="Failed to send Discord message")
    
    return {"message": f"Reminder sent to {len(pending_users)} pending users"}
