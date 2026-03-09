"""日程調整APIエンドポイント."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import get_db
from src.dependencies.auth import get_current_user_dep
from src.db.models import User, TheaterProject, ProjectMember, SchedulePoll, SchedulePollCandidate, Rehearsal, RehearsalScene, RehearsalSchedule, RehearsalCast, RehearsalParticipant, CharacterCasting
from src.schemas.schedule_poll import (
    SchedulePollCreate, SchedulePollResponse, SchedulePollAnswerUpdate, 
    SchedulePollFinalize, SchedulePollCalendarAnalysis,
    UnansweredMemberResponse, RemindUnansweredRequest
)
from src.services.schedule_poll_service import get_schedule_poll_service
from src.services.discord import get_discord_service, DiscordService
from src.services.attendance import AttendanceService
from datetime import datetime, timezone, timedelta

router = APIRouter()

@router.post("/projects/{project_id}/polls", response_model=SchedulePollResponse)
async def create_poll(
    project_id: UUID,
    payload: SchedulePollCreate,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service = Depends(get_discord_service),
):
    """日程調整を作成."""
    # 権限チェック (Editor以上)
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
        raise HTTPException(status_code=403, detail="操作権限がありません")

    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    poll_service = get_schedule_poll_service(db, discord_service)
    candidates_data = [c.model_dump() for c in payload.candidates]
    
    poll = await poll_service.create_poll(
        project=project,
        title=payload.title,
        description=payload.description,
        candidates_data=candidates_data,
        creator_id=current_user.id,
        required_roles=payload.required_roles,
        deadline=payload.deadline
    )
    return poll

@router.get("/projects/{project_id}/polls", response_model=list[SchedulePollResponse])
async def list_polls(
    project_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """プロジェクトの日程調整一覧を取得."""
    # 読み取り権限チェック
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    stmt = select(SchedulePoll).where(SchedulePoll.project_id == project_id).options(
        selectinload(SchedulePoll.candidates).selectinload(SchedulePollCandidate.answers)
    ).order_by(SchedulePoll.created_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/projects/{project_id}/polls/{poll_id}", response_model=SchedulePollResponse)
async def get_poll(
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """日程調整の詳細を取得."""
    poll_service = get_schedule_poll_service(db, None)
    poll = await poll_service.get_poll_with_details(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")
    
    # プロジェクトメンバーかチェック
    stmt = select(ProjectMember).where(ProjectMember.project_id == poll.project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
         raise HTTPException(status_code=403, detail="アクセス権限がありません")

    return poll

@router.get("/projects/{project_id}/polls/{poll_id}/recommendations")
async def get_poll_recommendations(
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """おすすめの日程とシーンを取得."""
    poll_service = get_schedule_poll_service(db, None)
    return await poll_service.get_recommendations(poll_id)

@router.get("/projects/{project_id}/polls/{poll_id}/calendar-analysis", response_model=SchedulePollCalendarAnalysis)
async def get_poll_calendar_analysis(
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """カレンダー表示用の詳細分析（正引き・リーチ判定込）を取得."""
    poll_service = get_schedule_poll_service(db, None)
    
    # 権限チェックは get_poll_with_details 等の中で行われるか、個別に必要なら追加
    # ここでは既存の get_poll と同様のチェックを行う
    poll = await poll_service.get_poll_with_details(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")
    
    stmt = select(ProjectMember).where(ProjectMember.project_id == poll.project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
         raise HTTPException(status_code=403, detail="アクセス権限がありません")

    result = await poll_service.get_calendar_analysis(poll_id)
    return result

@router.post("/projects/{project_id}/polls/{poll_id}/candidates/{candidate_id}/answer")
async def answer_poll(
    project_id: UUID,
    candidate_id: UUID,
    payload: SchedulePollAnswerUpdate,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """日程調整に回答."""
    # 権限チェック (viewer は回答不可)
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
        raise HTTPException(status_code=403, detail="閲覧者は日程調整に回答できません")

    poll_service = get_schedule_poll_service(db, None)
    await poll_service.upsert_answer(candidate_id, current_user.id, payload.status)
    return {"status": "ok"}

@router.post("/projects/{project_id}/polls/{poll_id}/finalize")
async def finalize_poll(
    project_id: UUID,
    poll_id: UUID,
    payload: SchedulePollFinalize,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
):
    """日程調整結果を元に稽古予定を作成."""
    # 権限チェック
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
         raise HTTPException(status_code=403, detail="操作権限がありません")

    candidate_id = payload.candidate_id
    scene_ids = payload.scene_ids

    # 候補日を取得 (回答も含めて取得)
    candidate_stmt = (
        select(SchedulePollCandidate)
        .where(SchedulePollCandidate.id == candidate_id)
        .options(selectinload(SchedulePollCandidate.answers))
    )
    candidate_result = await db.execute(candidate_stmt)
    candidate = candidate_result.scalar_one_or_none()
    
    if not candidate or candidate.poll_id != poll_id:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # スケジュールを取得（なければ作成）
    stmt = select(RehearsalSchedule).where(RehearsalSchedule.project_id == project_id).limit(1)
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()
    
    if not schedule:
        # 最新の脚本を取得
        from src.db.models import Script
        script_stmt = select(Script).where(Script.project_id == project_id).order_by(Script.revision.desc()).limit(1)
        script = (await db.execute(script_stmt)).scalar_one_or_none()
        if not script:
            raise HTTPException(status_code=400, detail="脚本が登録されていません")
            
        schedule = RehearsalSchedule(project_id=project_id, script_id=script.id)
        db.add(schedule)
        await db.flush()

    # 稽古レコード作成
    rehearsal = Rehearsal(
        schedule_id=schedule.id,
        date=candidate.start_datetime,
        duration_minutes=int((candidate.end_datetime - candidate.start_datetime).total_seconds() / 60),
        location="未定",
        notes=f"日程調整({poll_id})より自動作成"
    )
    db.add(rehearsal)
    await db.flush()

    # シーン紐付け
    for sid in scene_ids:
        db.add(RehearsalScene(rehearsal_id=rehearsal.id, scene_id=sid))
    
    # 参加者・キャストの自動登録ロジック (既存のadd_rehearsal互換のため最低限保持)
    await db.commit()
    
    project = await db.get(TheaterProject, project_id)

    # 対象ユーザー（候補日程でOK/Maybeと回答したメンバー、または全員など）
    attendance_targets = None # 全員対象
    if payload.attendance_target == "voters_only":
        # 候補にOK/Maybeで回答したユーザーのIDを抽出
        answered_users = [a.user_id for a in candidate.answers if a.status in ("ok", "maybe")]
        if answered_users:
            attendance_targets = answered_users
        else:
             # OK/Maybeの人がいなければ空リストか、あるいはフォールバックで全員？
             # ここは誰も行けない予定を確定したという意味になるので、あえて誰も呼ばない（空リストはcreate_attendance側でどうなるか）
             # create_attendance_event は target_user_ids=None で全員になる。
             # [] を渡すと誰も呼ばないが、Discordユーザー0人扱いでスキップされるかもしれない
             attendance_targets = [] 

    # 出欠確認イベントの作成
    if attendance_targets is None or attendance_targets:
        attendance_service = AttendanceService(db, discord_service)
        deadline = rehearsal.date - timedelta(hours=24)
        
        await attendance_service.create_attendance_event(
            project=project,
            title=f"稽古: {rehearsal.date.astimezone().strftime('%m/%d %H:%M')}",
            deadline=deadline,
            schedule_date=rehearsal.date,
            location=rehearsal.location,
            description=rehearsal.notes,
            target_user_ids=attendance_targets
        )

    # Discord通知
    if project and project.discord_webhook_url:
        rehearsal_ts = int(rehearsal.date.replace(tzinfo=timezone.utc).timestamp())
        date_str = f"<t:{rehearsal_ts}:f>" # User local time
        content = f"📅 **日程調整の結果、稽古が確定しました**\n日時: {date_str}\n場所: {rehearsal.location or '未定'}"
        
        now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        start_dt = rehearsal.date.astimezone(timezone.utc)
        start_str = start_dt.strftime("%Y%m%dT%H%M%SZ")
        end_dt = start_dt + timedelta(minutes=rehearsal.duration_minutes)
        end_str = end_dt.strftime("%Y%m%dT%H%M%SZ")
        
        ics_content = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//PSCWeb3//Rehearsal Schedule//EN\r\n"
            "CALSCALE:GREGORIAN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{rehearsal.id}@pscweb3.local\r\n"
            f"DTSTAMP:{now_str}\r\n"
            f"DTSTART:{start_str}\r\n"
            f"DTEND:{end_str}\r\n"
            f"SUMMARY:📌 稽古確定 - {project.name}\r\n"
            f"DESCRIPTION:日程調整により稽古が確定しました。\\n場所: {rehearsal.location or '未定'}\r\n"
            f"LOCATION:{rehearsal.location or '未定'}\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        ics_file = {
            "filename": "rehearsal.ics",
            "content": ics_content.encode("utf-8")
        }

        background_tasks.add_task(
            discord_service.send_notification,
            content=content,
            webhook_url=project.discord_webhook_url,
            file=ics_file,
        )

    return {"status": "ok", "rehearsal_id": rehearsal.id}

@router.get("/projects/{project_id}/polls/{poll_id}/unanswered", response_model=list[UnansweredMemberResponse])
async def get_unanswered_members(
    project_id: UUID,
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """未回答メンバー一覧を取得."""
    # 権限チェック
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
         raise HTTPException(status_code=403, detail="アクセス権限がありません")

    poll_service = get_schedule_poll_service(db, None)
    return await poll_service.get_unanswered_members(poll_id)

@router.post("/projects/{project_id}/polls/{poll_id}/remind")
async def remind_unanswered_members(
    project_id: UUID,
    poll_id: UUID,
    payload: RemindUnansweredRequest,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service = Depends(get_discord_service),
):
    """未回答メンバーにリマインドを送信."""
    # 権限チェック
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
        raise HTTPException(status_code=403, detail="操作権限がありません")

    from src.config import settings
    base_url = settings.frontend_url or "https://pscweb3.azurewebsites.net"

    poll_service = get_schedule_poll_service(db, discord_service)
    await poll_service.send_reminder(poll_id, payload.target_user_ids, base_url)
    return {"status": "ok"}

@router.post("/projects/{project_id}/polls/{poll_id}/stop-reminder")
async def stop_poll_reminder(
    project_id: UUID,
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """自動リマインドを停止."""
    # 権限チェック (Editor以上)
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
         raise HTTPException(status_code=403, detail="操作権限がありません")

    poll_service = get_schedule_poll_service(db, None)
    success = await poll_service.stop_auto_reminder(poll_id)
    if not success:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")
    
    return {"status": "ok"}

@router.delete("/projects/{project_id}/polls/{poll_id}")
async def delete_poll(
    project_id: UUID,
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """日程調整を削除."""
    # 権限チェック (Editor以上)
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
         raise HTTPException(status_code=403, detail="操作権限がありません")

    # 日程調整を取得
    poll = await db.get(SchedulePoll, poll_id)
    if not poll or poll.project_id != project_id:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")

    await db.delete(poll)
    await db.commit()

    return {"status": "ok"}
