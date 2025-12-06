"""稽古スケジュール管理APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user_dep
from src.db import get_db
from src.services.discord import DiscordService, get_discord_service
from src.db.models import (
    ProjectMember,
    Rehearsal,
    RehearsalParticipant,
    RehearsalSchedule,
    Scene,
    Script,
    User,
    TheaterProject
)
from src.schemas.rehearsal import (
    RehearsalCastResponse,
    RehearsalCreate,
    RehearsalParticipantResponse,
    RehearsalResponse,
    RehearsalScheduleResponse,
    RehearsalUpdate,
)

router = APIRouter()


@router.post("/projects/{project_id}/rehearsal-schedule", response_model=RehearsalScheduleResponse)
async def create_rehearsal_schedule(
    project_id: int,
    background_tasks: BackgroundTasks,
    script_id: int = Query(...),
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> RehearsalScheduleResponse:
    """稽古スケジュールを作成.

    Args:
        project_id: プロジェクトID
        background_tasks: バックグラウンドタスク
        script_id: 脚本ID
        current_user: 認証ユーザー
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        RehearsalScheduleResponse: 作成されたスケジュール

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="スケジュール作成の権限がありません")

    # 脚本存在確認
    result = await db.execute(
        select(Script).where(Script.id == script_id, Script.project_id == project_id)
    )
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # スケジュール作成
    schedule = RehearsalSchedule(
        project_id=project_id,
        script_id=script_id,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    # Discord通知
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"📅 **新しい稽古スケジュールが作成されました**\nプロジェクト: {project.name}\n対象脚本: {script.title}",
        webhook_url=project.discord_webhook_url,
    )

    return RehearsalScheduleResponse(
        id=schedule.id,
        project_id=schedule.project_id,
        script_id=schedule.script_id,
        script_title=script.title,
        created_at=schedule.created_at,
        rehearsals=[],
    )


@router.get("/projects/{project_id}/rehearsal-schedule", response_model=RehearsalScheduleResponse)
async def get_rehearsal_schedule(
    project_id: int,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> RehearsalScheduleResponse:
    """稽古スケジュールを取得.

    Args:
        project_id: プロジェクトID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        RehearsalScheduleResponse: スケジュール

    Raises:
        HTTPException: 認証エラーまたはスケジュールが見つからない
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # スケジュール取得
    result = await db.execute(
        select(RehearsalSchedule).where(RehearsalSchedule.project_id == project_id)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="稽古スケジュールが見つかりません")

    # 脚本取得
    result = await db.execute(select(Script).where(Script.id == schedule.script_id))
    script = result.scalar_one()

    # 稽古一覧を整形
    rehearsal_responses = []
    for rehearsal in schedule.rehearsals:
        # シーン情報
        scene_heading = None
        if rehearsal.scene_id:
            result = await db.execute(select(Scene).where(Scene.id == rehearsal.scene_id))
            scene = result.scalar_one_or_none()
            if scene:
                scene_heading = scene.heading

        # 参加者
        participants = []
        for p in rehearsal.participants:
            result = await db.execute(select(User).where(User.id == p.user_id))
            participant_user = result.scalar_one()
            participants.append(
                RehearsalParticipantResponse(
                    user_id=participant_user.id,
                    user_name=participant_user.discord_username,
                )
            )

        # キャスト
        casts = []
        for c in rehearsal.casts:
            # Characterとリレーション再取得が必要
            cast_dict = {
                "character_id": c.character_id,
                "character_name": c.character.name,
                "user_id": c.user_id,
                "user_name": c.user.discord_username,
            }
            casts.append(RehearsalCastResponse(**cast_dict))

        rehearsal_responses.append(
            RehearsalResponse(
                id=rehearsal.id,
                schedule_id=rehearsal.schedule_id,
                scene_id=rehearsal.scene_id,
                scene_heading=scene_heading,
                date=rehearsal.date,
                duration_minutes=rehearsal.duration_minutes,
                location=rehearsal.location,
                notes=rehearsal.notes,
                participants=participants,
                casts=casts,
            )
        )

    return RehearsalScheduleResponse(
        id=schedule.id,
        project_id=schedule.project_id,
        script_id=schedule.script_id,
        script_title=script.title,
        created_at=schedule.created_at,
        rehearsals=rehearsal_responses,
    )


@router.post("/schedules/{schedule_id}/rehearsals", response_model=RehearsalResponse)
async def add_rehearsal(
    schedule_id: int,
    rehearsal_data: RehearsalCreate,
    background_tasks: BackgroundTasks,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> RehearsalResponse:
    """稽古を追加.

    Args:
        schedule_id: スケジュールID
        rehearsal_data: 稽古データ
        background_tasks: バックグラウンドタスク
        current_user: 認証ユーザー
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        RehearsalResponse: 追加された稽古

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # スケジュール取得
    result = await db.execute(
        select(RehearsalSchedule).where(RehearsalSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == schedule.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="稽古追加の権限がありません")

    # 稽古作成
    rehearsal = Rehearsal(
        schedule_id=schedule_id,
        scene_id=rehearsal_data.scene_id,
        date=rehearsal_data.date,
        duration_minutes=rehearsal_data.duration_minutes,
        location=rehearsal_data.location,
        notes=rehearsal_data.notes,
    )
    db.add(rehearsal)
    await db.commit()
    await db.refresh(rehearsal)

    # シーン情報
    scene_heading = None
    if rehearsal.scene_id:
        result = await db.execute(select(Scene).where(Scene.id == rehearsal.scene_id))
        scene = result.scalar_one_or_none()
        if scene:
            scene_heading = scene.heading

    # Discord通知
    project = await db.get(TheaterProject, schedule.project_id)
    
    date_str = rehearsal.date.strftime("%Y/%m/%d %H:%M")
    content = f"📅 **実習(稽古)が追加されました**\n日時: {date_str}\n場所: {rehearsal.location or '未定'}"
    if scene_heading:
        content += f"\nシーン: {scene_heading}"
        
    background_tasks.add_task(
        discord_service.send_notification,
        content=content,
        webhook_url=project.discord_webhook_url,
    )

    return RehearsalResponse(
        id=rehearsal.id,
        schedule_id=rehearsal.schedule_id,
        scene_id=rehearsal.scene_id,
        scene_heading=scene_heading,
        date=rehearsal.date,
        duration_minutes=rehearsal.duration_minutes,
        location=rehearsal.location,
        notes=rehearsal.notes,
        participants=[],
        casts=[],
    )


@router.put("/rehearsals/{rehearsal_id}", response_model=RehearsalResponse)
async def update_rehearsal(
    rehearsal_id: int,
    rehearsal_data: RehearsalUpdate,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> RehearsalResponse:
    """稽古を更新.

    Args:
        rehearsal_id: 稽古ID
        rehearsal_data: 更新データ
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        RehearsalResponse: 更新された稽古

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 稽古取得
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if rehearsal is None:
        raise HTTPException(status_code=404, detail="稽古が見つかりません")

    # スケジュール取得
    result = await db.execute(
        select(RehearsalSchedule).where(RehearsalSchedule.id == rehearsal.schedule_id)
    )
    schedule = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == schedule.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="稽古更新の権限がありません")

    # 更新
    if rehearsal_data.scene_id is not None:
        rehearsal.scene_id = rehearsal_data.scene_id
    if rehearsal_data.date is not None:
        rehearsal.date = rehearsal_data.date
    if rehearsal_data.duration_minutes is not None:
        rehearsal.duration_minutes = rehearsal_data.duration_minutes
    if rehearsal_data.location is not None:
        rehearsal.location = rehearsal_data.location
    if rehearsal_data.notes is not None:
        rehearsal.notes = rehearsal_data.notes

    await db.commit()
    await db.refresh(rehearsal)

    # シーン情報
    scene_heading = None
    if rehearsal.scene_id:
        result = await db.execute(select(Scene).where(Scene.id == rehearsal.scene_id))
        scene = result.scalar_one_or_none()
        if scene:
            scene_heading = scene.heading

    return RehearsalResponse(
        id=rehearsal.id,
        schedule_id=rehearsal.schedule_id,
        scene_id=rehearsal.scene_id,
        scene_heading=scene_heading,
        date=rehearsal.date,
        duration_minutes=rehearsal.duration_minutes,
        location=rehearsal.location,
        notes=rehearsal.notes,
        participants=[p for p in rehearsal.participants],
        casts=[c for c in rehearsal.casts],
    )


@router.post("/rehearsals/{rehearsal_id}/participants/{user_id}")
async def add_participant(
    rehearsal_id: int,
    user_id: int,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """稽古に参加者を追加.

    Args:
        rehearsal_id: 稽古ID
        user_id: ユーザーID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        dict: 成功メッセージ

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 稽古取得
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if rehearsal is None:
        raise HTTPException(status_code=404, detail="稽古が見つかりません")

    # 参加者追加
    participant = RehearsalParticipant(
        rehearsal_id=rehearsal_id,
        user_id=user_id,
    )
    db.add(participant)
    await db.commit()

    return {"message": "参加者を追加しました"}


@router.delete("/rehearsals/{rehearsal_id}")
async def delete_rehearsal(
    rehearsal_id: int,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """稽古を削除.

    Args:
        rehearsal_id: 稽古ID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        dict: 成功メッセージ

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 稽古取得
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if rehearsal is None:
        raise HTTPException(status_code=404, detail="稽古が見つかりません")

    # スケジュール取得
    result = await db.execute(
        select(RehearsalSchedule).where(RehearsalSchedule.id == rehearsal.schedule_id)
    )
    schedule = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == schedule.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="稽古削除の権限がありません")

    # 削除
    await db.delete(rehearsal)
    await db.commit()

    return {"message": "稽古を削除しました"}
