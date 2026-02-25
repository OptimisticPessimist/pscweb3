"""日程調整APIエンドポイント."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import get_db
from src.dependencies.auth import get_current_user_dep
from src.db.models import User, TheaterProject, ProjectMember, SchedulePoll, SchedulePollCandidate, Rehearsal, RehearsalScene, RehearsalSchedule, RehearsalCast, RehearsalParticipant, CharacterCasting
from src.schemas.schedule_poll import SchedulePollCreate, SchedulePollResponse, SchedulePollAnswerUpdate, SchedulePollFinalize
from src.services.schedule_poll_service import get_schedule_poll_service
from src.services.discord import get_discord_service

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
        creator_id=current_user.id
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

@router.post("/projects/{project_id}/polls/{poll_id}/candidates/{candidate_id}/answer")
async def answer_poll(
    candidate_id: UUID,
    payload: SchedulePollAnswerUpdate,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """日程調整に回答."""
    poll_service = get_schedule_poll_service(db, None)
    await poll_service.upsert_answer(candidate_id, current_user.id, payload.status)
    return {"status": "ok"}

@router.post("/projects/{project_id}/polls/{poll_id}/finalize")
async def finalize_poll(
    project_id: UUID,
    poll_id: UUID,
    payload: SchedulePollFinalize,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
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

    # 候補日を取得
    candidate = await db.get(SchedulePollCandidate, candidate_id)
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
    
    #TODO: キャスト・参加者の自動登録ロジック (既存のadd_rehearsalを参考にするのが良いが、一旦シンプルに)
    
    await db.commit()
    return {"status": "ok", "rehearsal_id": rehearsal.id}
