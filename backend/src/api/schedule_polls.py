"""日程調整APIエンドポイント."""

from datetime import UTC, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import (
    ProjectMember,
    Rehearsal,
    RehearsalScene,
    RehearsalSchedule,
    Scene,
    SchedulePoll,
    SchedulePollCandidate,
    Script,
    TheaterProject,
    User,
)
from src.dependencies.auth import get_current_user_dep
from src.schemas.schedule_poll import (
    RemindUnansweredRequest,
    SchedulePollAnswerUpdate,
    SchedulePollCalendarAnalysis,
    SchedulePollCreate,
    SchedulePollFinalize,
    SchedulePollFinalizeBatchRequest,
    SchedulePollFinalizeBatchResponse,
    SchedulePollFinalizeBatchResult,
    SchedulePollFinalizeResponse,
    SchedulePollResponse,
    SchedulePollUpdateRequiredRoles,
    UnansweredMemberResponse,
)
from src.services.attendance import AttendanceService
from src.services.calendar_url import build_google_calendar_url
from src.services.discord import DiscordService, get_discord_service
from src.services.schedule_poll_service import get_schedule_poll_service

router = APIRouter()


def _serialize_poll_for_member(
    poll: SchedulePoll,
    member: ProjectMember,
    current_user_id: UUID,
) -> SchedulePollResponse:
    """メンバー権限に応じて日程調整レスポンスを整形."""
    response = SchedulePollResponse.model_validate(poll)
    if member.role == "viewer":
        for candidate in response.candidates:
            candidate.answers = [a for a in candidate.answers if a.user_id == current_user_id]
    return response


async def _get_or_create_rehearsal_schedule(
    db: AsyncSession, project_id: UUID
) -> RehearsalSchedule:
    """稽古スケジュールを取得（なければ最新脚本で作成）."""
    stmt = select(RehearsalSchedule).where(RehearsalSchedule.project_id == project_id).limit(1)
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()

    if schedule:
        return schedule

    script_stmt = (
        select(Script).where(Script.project_id == project_id).order_by(Script.revision.desc()).limit(1)
    )
    script = (await db.execute(script_stmt)).scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=400, detail="脚本が登録されていません")

    schedule = RehearsalSchedule(project_id=project_id, script_id=script.id)
    db.add(schedule)
    await db.flush()
    return schedule


async def _finalize_poll_candidate(
    *,
    project_id: UUID,
    poll_id: UUID,
    payload: SchedulePollFinalize,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
    discord_service: DiscordService,
    schedule: RehearsalSchedule,
    project: TheaterProject | None,
) -> dict:
    """候補1件から稽古を作成し、通知情報を返す."""
    candidate_stmt = (
        select(SchedulePollCandidate)
        .where(SchedulePollCandidate.id == payload.candidate_id)
        .options(selectinload(SchedulePollCandidate.answers))
    )
    candidate_result = await db.execute(candidate_stmt)
    candidate = candidate_result.scalar_one_or_none()

    if not candidate or candidate.poll_id != poll_id:
        raise HTTPException(status_code=404, detail="Candidate not found")

    scene_ids = payload.scene_ids
    rehearsal_title = payload.rehearsal_title.strip() if payload.rehearsal_title else None
    rehearsal_location = payload.location.strip() if payload.location else ""
    if not rehearsal_location:
        rehearsal_location = "未定"
    rehearsal_notes = payload.notes.strip() if payload.notes else None
    duration_minutes = int((candidate.end_datetime - candidate.start_datetime).total_seconds() / 60)

    # 重複登録ガード（同一候補・同一内容の再登録を抑止）
    existing_rehearsals_stmt = (
        select(Rehearsal)
        .where(
            Rehearsal.schedule_id == schedule.id,
            Rehearsal.date == candidate.start_datetime,
            Rehearsal.duration_minutes == duration_minutes,
            Rehearsal.title == rehearsal_title,
            Rehearsal.location == rehearsal_location,
        )
        .options(selectinload(Rehearsal.scenes))
    )
    existing_rehearsals = (await db.execute(existing_rehearsals_stmt)).scalars().all()
    requested_scene_ids = set(scene_ids)
    for existing in existing_rehearsals:
        existing_scene_ids = {scene.id for scene in existing.scenes}
        if existing_scene_ids == requested_scene_ids:
            existing_scene_text = ", ".join(
                f"#{f'{s.act_number}-{s.scene_number}' if s.act_number else str(s.scene_number)} {s.heading}"
                for s in existing.scenes
            )
            existing_gcal_url = None
            if project:
                existing_start_dt = existing.date.astimezone(UTC)
                existing_end_dt = existing_start_dt + timedelta(minutes=existing.duration_minutes)
                existing_gcal_url = build_google_calendar_url(
                    title=existing.title or f"稽古確定 - {project.name}",
                    start_dt=existing_start_dt,
                    end_dt=existing_end_dt,
                    description=f"日程調整により稽古が確定しました。\n{'シーン: ' + existing_scene_text if existing_scene_text else ''}\n場所: {existing.location or '未定'}",
                    location=existing.location or "",
                )
            return {
                "status": "already_exists",
                "rehearsal_id": existing.id,
                "gcal_url": existing_gcal_url,
            }

    rehearsal = Rehearsal(
        schedule_id=schedule.id,
        title=rehearsal_title,
        date=candidate.start_datetime,
        duration_minutes=duration_minutes,
        location=rehearsal_location,
        notes=rehearsal_notes or f"日程調整({poll_id})より自動作成",
    )
    db.add(rehearsal)
    await db.flush()

    for sid in scene_ids:
        db.add(RehearsalScene(rehearsal_id=rehearsal.id, scene_id=sid))

    await db.commit()

    attendance_targets = None  # 全員対象
    if payload.attendance_target == "voters_only":
        answered_users = [a.user_id for a in candidate.answers if a.status in ("ok", "maybe")]
        attendance_targets = answered_users if answered_users else []

    scenes_db = await db.execute(select(Scene).where(Scene.id.in_(scene_ids)))
    scenes = scenes_db.scalars().all()
    scene_headings = []
    for s in scenes:
        act_scene = f"{s.act_number}-{s.scene_number}" if s.act_number else str(s.scene_number)
        scene_headings.append(f"#{act_scene} {s.heading}")
    scene_text = ", ".join(scene_headings) if scene_headings else None

    if attendance_targets is None or attendance_targets:
        attendance_service = AttendanceService(db, discord_service)
        deadline = rehearsal.date - timedelta(hours=24)
        attendance_title = (
            f"稽古: {rehearsal.title}"
            if rehearsal.title
            else f"稽古: {rehearsal.date.replace(tzinfo=UTC).astimezone(timezone(timedelta(hours=9))).strftime('%m/%d %H:%M')}"
            + (f" ({scene_text})" if scene_text else "")
        )

        await attendance_service.create_attendance_event(
            project=project,
            title=attendance_title,
            deadline=deadline,
            schedule_date=rehearsal.date,
            location=rehearsal.location,
            description=rehearsal.notes,
            target_user_ids=attendance_targets,
        )

    gcal_url = None
    if project:
        start_dt = rehearsal.date.astimezone(UTC)
        end_dt = start_dt + timedelta(minutes=rehearsal.duration_minutes)
        gcal_url = build_google_calendar_url(
            title=rehearsal.title or f"稽古確定 - {project.name}",
            start_dt=start_dt,
            end_dt=end_dt,
            description=f"日程調整により稽古が確定しました。\n{'シーン: ' + scene_text if scene_text else ''}\n場所: {rehearsal.location or '未定'}",
            location=rehearsal.location or "",
        )

    if project and project.discord_webhook_url:
        rehearsal_ts = int(rehearsal.date.replace(tzinfo=UTC).timestamp())
        date_str = f"<t:{rehearsal_ts}:f>"  # User local time
        content = f"📅 **日程調整の結果、稽古が確定しました**\n日時: {date_str}\n場所: {rehearsal.location or '未定'}"
        if rehearsal.title:
            content += f"\nタイトル: {rehearsal.title}"
        if scene_text:
            content += f"\nシーン: {scene_text}"
        content += f"\n📎 Googleカレンダーに追加: {gcal_url}"

        background_tasks.add_task(
            discord_service.send_notification,
            content=content,
            webhook_url=project.discord_webhook_url,
        )

    return {"status": "created", "rehearsal_id": rehearsal.id, "gcal_url": gcal_url}


@router.post("/projects/{project_id}/polls", response_model=SchedulePollResponse)
async def create_poll(
    project_id: UUID,
    payload: SchedulePollCreate,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service=Depends(get_discord_service),
):
    """日程調整を作成."""
    # 権限チェック (Editor以上)
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
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
        deadline=payload.deadline,
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
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    stmt = (
        select(SchedulePoll)
        .where(SchedulePoll.project_id == project_id)
        .options(selectinload(SchedulePoll.candidates).selectinload(SchedulePollCandidate.answers))
        .order_by(SchedulePoll.created_at.desc())
    )

    result = await db.execute(stmt)
    polls = result.scalars().all()
    return [_serialize_poll_for_member(poll, member, current_user.id) for poll in polls]


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
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == poll.project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    return _serialize_poll_for_member(poll, member, current_user.id)


@router.patch("/projects/{project_id}/polls/{poll_id}", response_model=SchedulePollResponse)
async def update_poll_required_roles(
    project_id: UUID,
    poll_id: UUID,
    payload: SchedulePollUpdateRequiredRoles,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
        raise HTTPException(status_code=403, detail="編集権限がありません")

    poll = await db.get(SchedulePoll, poll_id)
    if not poll or poll.project_id != project_id:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")

    poll_service = get_schedule_poll_service(db, None)
    updated_poll = await poll_service.update_required_roles(poll_id, payload.required_roles)
    if not updated_poll:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")

    return updated_poll


@router.get("/projects/{project_id}/polls/{poll_id}/recommendations")
async def get_poll_recommendations(
    project_id: UUID,
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """おすすめの日程とシーンを取得."""
    poll = await db.get(SchedulePoll, poll_id)
    if not poll or poll.project_id != project_id:
        raise HTTPException(status_code=404, detail="日程調整が見つかりません")

    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")
    if member.role == "viewer":
        raise HTTPException(status_code=403, detail="閲覧専用メンバーはおすすめ分析を閲覧できません")

    poll_service = get_schedule_poll_service(db, None)
    return await poll_service.get_recommendations(poll_id)


@router.get(
    "/projects/{project_id}/polls/{poll_id}/calendar-analysis",
    response_model=SchedulePollCalendarAnalysis,
)
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

    stmt = select(ProjectMember).where(
        ProjectMember.project_id == poll.project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")
    if member.role == "viewer":
        raise HTTPException(status_code=403, detail="閲覧専用メンバーは詳細分析を閲覧できません")

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
    # 権限チェック
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="プロジェクトメンバーではありません")

    poll_service = get_schedule_poll_service(db, None)
    await poll_service.upsert_answer(candidate_id, current_user.id, payload.status)
    return {"status": "ok"}


@router.post(
    "/projects/{project_id}/polls/{poll_id}/finalize",
    response_model=SchedulePollFinalizeResponse,
)
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
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
        raise HTTPException(status_code=403, detail="操作権限がありません")
    schedule = await _get_or_create_rehearsal_schedule(db, project_id)
    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    return await _finalize_poll_candidate(
        project_id=project_id,
        poll_id=poll_id,
        payload=payload,
        background_tasks=background_tasks,
        db=db,
        discord_service=discord_service,
        schedule=schedule,
        project=project,
    )


@router.post(
    "/projects/{project_id}/polls/{poll_id}/finalize-batch",
    response_model=SchedulePollFinalizeBatchResponse,
)
async def finalize_poll_batch(
    project_id: UUID,
    poll_id: UUID,
    payload: SchedulePollFinalizeBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
):
    """日程調整結果を元に複数の稽古予定を一括作成."""
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()
    if not member or member.role == "viewer":
        raise HTTPException(status_code=403, detail="操作権限がありません")

    if not payload.items:
        raise HTTPException(status_code=400, detail="登録対象がありません")

    schedule = await _get_or_create_rehearsal_schedule(db, project_id)
    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    results: list[SchedulePollFinalizeBatchResult] = []
    created_count = 0
    already_exists_count = 0
    error_count = 0

    for item in payload.items:
        try:
            finalized = await _finalize_poll_candidate(
                project_id=project_id,
                poll_id=poll_id,
                payload=item,
                background_tasks=background_tasks,
                db=db,
                discord_service=discord_service,
                schedule=schedule,
                project=project,
            )
            finalized_status = finalized["status"]
            if finalized_status == "already_exists":
                already_exists_count += 1
            else:
                created_count += 1
            results.append(
                SchedulePollFinalizeBatchResult(
                    candidate_id=item.candidate_id,
                    status=finalized_status,
                    rehearsal_id=finalized["rehearsal_id"],
                    gcal_url=finalized["gcal_url"],
                )
            )
        except HTTPException as e:
            await db.rollback()
            error_count += 1
            results.append(
                SchedulePollFinalizeBatchResult(
                    candidate_id=item.candidate_id,
                    status="error",
                    error=str(e.detail),
                )
            )
        except Exception as e:
            await db.rollback()
            error_count += 1
            results.append(
                SchedulePollFinalizeBatchResult(
                    candidate_id=item.candidate_id,
                    status="error",
                    error=str(e),
                )
            )

    return SchedulePollFinalizeBatchResponse(
        created_count=created_count,
        already_exists_count=already_exists_count,
        error_count=error_count,
        results=results,
    )


@router.get(
    "/projects/{project_id}/polls/{poll_id}/unanswered",
    response_model=list[UnansweredMemberResponse],
)
async def get_unanswered_members(
    project_id: UUID,
    poll_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """未回答メンバー一覧を取得."""
    # 権限チェック
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
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
    discord_service=Depends(get_discord_service),
):
    """未回答メンバーにリマインドを送信."""
    # 権限チェック
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
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
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
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
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
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
