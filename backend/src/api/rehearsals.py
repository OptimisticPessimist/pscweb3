"""稽古スケジュール管理APIエンドポイント."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog import get_logger

from src.dependencies.auth import get_current_user_dep
from src.db import get_db
from src.services.discord import DiscordService, get_discord_service
from src.services.attendance import AttendanceService
from src.db.models import (
    ProjectMember,
    Rehearsal,
    RehearsalCast,
    RehearsalParticipant,
    RehearsalSchedule,
    RehearsalScene,
    Scene,
    Script,
    User,
    TheaterProject,
    Line,
    Character,
    CharacterCasting,
    AttendanceEvent,
    AttendanceTarget,
)
from datetime import timedelta
from src.schemas.rehearsal import (
    RehearsalCastCreate,
    RehearsalCastResponse,
    RehearsalCreate,
    RehearsalParticipantResponse,
    RehearsalResponse,
    RehearsalScheduleResponse,
    RehearsalUpdate,
    RehearsalParticipantUpdate,
)
from src.services.attendance import AttendanceService

router = APIRouter()
project_router = APIRouter()



@project_router.post("/{project_id}/rehearsal-schedule", response_model=RehearsalScheduleResponse)
async def create_rehearsal_schedule(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    script_id: UUID = Query(...),
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




@project_router.get("/{project_id}/rehearsal-schedule", response_model=RehearsalScheduleResponse)
async def get_rehearsal_schedule(
    project_id: UUID,
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
        select(RehearsalSchedule)
        .where(RehearsalSchedule.project_id == project_id)
        .options(
            selectinload(RehearsalSchedule.rehearsals).options(
                selectinload(Rehearsal.participants),
                selectinload(Rehearsal.casts).options(
                    selectinload(RehearsalCast.character),
                    selectinload(RehearsalCast.user)
                )
            )
        )
    )
    # 重複データがある場合、有効な（脚本が存在する）スケジュールを探す
    schedules = result.scalars().all()
    
    schedule = None
    script = None
    
    for s in schedules:
        script_res = await db.execute(select(Script).where(Script.id == s.script_id))
        found_script = script_res.scalar_one_or_none()
        if found_script:
            schedule = s
            script = found_script
            break
            
    if schedule is None:
        raise HTTPException(status_code=404, detail="稽古スケジュールが見つかりません")
    
    # scriptはループ内で既に取得済み

    # プロジェクトメンバー情報を取得して、user_id -> display_name のマップを作成
    member_result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    members = member_result.scalars().all()
    display_name_map = {m.user_id: m.display_name for m in members}
    
    # User Map creation to avoid MissingGreenlet on p.user.discord_username access
    all_user_ids = set()
    for rehearsal in schedule.rehearsals:
        for p in rehearsal.participants:
            all_user_ids.add(p.user_id)
        for c in rehearsal.casts:
            all_user_ids.add(c.user_id)
        # Default casts users
        if rehearsal.scene_id:
             result = await db.execute(
                select(Scene)
                .where(Scene.id == rehearsal.scene_id)
                .options(
                    selectinload(Scene.lines).options(
                        selectinload(Line.character).options(
                            selectinload(Character.castings)
                        )
                    )
                )
            )
             scene = result.scalar_one_or_none()
             if scene:
                for line in scene.lines:
                    if line.character:
                        for casting in line.character.castings:
                            all_user_ids.add(casting.user_id)

    user_map = {}
    if all_user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(all_user_ids)))
        users = user_result.scalars().all()
        user_map = {u.id: u for u in users}

    # 稽古一覧を整形
    rehearsal_responses = []
    for rehearsal in schedule.rehearsals:
        # シーン情報
        scene_heading = None
        if rehearsal.scene_id:
            result = await db.execute(
                select(Scene)
                .where(Scene.id == rehearsal.scene_id)
                .options(
                    selectinload(Scene.lines).options(
                        selectinload(Line.character).options(
                            selectinload(Character.castings)
                        )
                    )
                )
            )
            scene = result.scalar_one_or_none()
            if scene:
                scene_heading = scene.heading

        # 参加者
        participants = []
        for p in rehearsal.participants:
            participant_user = user_map.get(p.user_id)
            if participant_user:
                participants.append(
                    RehearsalParticipantResponse(
                        user_id=participant_user.id,
                        user_name=participant_user.discord_username,
                        display_name=display_name_map.get(participant_user.id),
                        staff_role=p.staff_role,
                    )
                )

        # キャスト
        casts_response_list = []
        rehearsal_cast_map = {c.character_id: c for c in rehearsal.casts}

        # 1. Add explicit rehearsal casts
        for rc in rehearsal.casts:
            rc_user = user_map.get(rc.user_id)
            if rc_user:
                casts_response_list.append(RehearsalCastResponse(
                    character_id=rc.character_id,
                    character_name=rc.character.name,
                    user_id=rc.user_id,
                    user_name=rc_user.discord_username,
                    display_name=display_name_map.get(rc.user_id)
                ))

        # 2. Add default casts for characters NOT in explicit list
        if rehearsal.scene_id:
            # シーン情報は上で取得済み (scene変数)
            if scene:
                # 登場人物をユニークにする
                unique_characters = {}
                for line in scene.lines:
                    if line.character_id and line.character and line.character_id not in unique_characters:
                        unique_characters[line.character_id] = line.character
                
                for char_id, char in unique_characters.items():
                    if char_id not in rehearsal_cast_map:
                        # デフォルト配役を追加
                        for casting in char.castings:
                            cast_user = user_map.get(casting.user_id)
                            if cast_user:
                                casts_response_list.append(RehearsalCastResponse(
                                    character_id=char.id,
                                    character_name=char.name,
                                    user_id=casting.user_id,
                                    user_name=cast_user.discord_username,
                                    display_name=display_name_map.get(casting.user_id)
                                ))

        rehearsal_responses.append(
            RehearsalResponse(
                id=rehearsal.id,
                schedule_id=rehearsal.schedule_id,
                scene_id=rehearsal.scene_id,
                scene_heading=scene_heading,
                date=rehearsal.date.replace(tzinfo=timezone.utc),
                duration_minutes=rehearsal.duration_minutes,
                location=rehearsal.location,
                notes=rehearsal.notes,
                participants=participants,
                casts=casts_response_list,
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
    schedule_id: UUID,
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
    logger = get_logger(__name__)
    logger.info("add_rehearsal called", schedule_id=str(schedule_id), create_attendance=rehearsal_data.create_attendance_check)
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

    # Naive UTC conversion for DB
    date_naive = rehearsal_data.date.replace(tzinfo=None) if rehearsal_data.date.tzinfo else rehearsal_data.date

    # 稽古作成
    # 稽古作成
    rehearsal = Rehearsal(
        schedule_id=schedule_id,
        # scene_idは非推奨だが、互換性のためにセット（最初の1つまたは指定されたもの）
        scene_id=rehearsal_data.scene_id or (rehearsal_data.scene_ids[0] if rehearsal_data.scene_ids else None),
        date=date_naive,
        duration_minutes=rehearsal_data.duration_minutes,
        location=rehearsal_data.location,
        notes=rehearsal_data.notes,
    )
    db.add(rehearsal)
    await db.flush() # ID生成のため

    # シーン紐付け (Multi-Scene)
    target_scene_ids = set()
    if rehearsal_data.scene_ids:
        target_scene_ids.update(rehearsal_data.scene_ids)
    elif rehearsal_data.scene_id:
        target_scene_ids.add(rehearsal_data.scene_id)
    
    if target_scene_ids:
        # Explicitly add to association table to avoid AsyncIO issues with relationship assignment
        for sid in target_scene_ids:
            db.add(RehearsalScene(rehearsal_id=rehearsal.id, scene_id=sid))

    # 参加者・キャスト登録
    target_user_ids = set()

    # Staffs
    if rehearsal_data.participants is not None:
        # 明示的な指定がある場合
        for p in rehearsal_data.participants:
            new_participant = RehearsalParticipant(
                rehearsal_id=rehearsal.id,
                user_id=p.user_id,
                staff_role=p.staff_role,
            )
            db.add(new_participant)
            target_user_ids.add(p.user_id)
    else:
        # Legacy: Default Staff Auto-Assignment
        member_result = await db.execute(
            select(ProjectMember).where(ProjectMember.project_id == schedule.project_id)
        )
        members = member_result.scalars().all()
        for m in members:
            if m.default_staff_role:
                new_participant = RehearsalParticipant(
                    rehearsal_id=rehearsal.id,
                    user_id=m.user_id,
                    staff_role=m.default_staff_role,
                )
                db.add(new_participant)
                target_user_ids.add(m.user_id)
    
    # Casts
    if rehearsal_data.casts is not None:
        for c in rehearsal_data.casts:
            new_cast = RehearsalCast(
                rehearsal_id=rehearsal.id,
                character_id=c.character_id,
                user_id=c.user_id
            )
            db.add(new_cast)
            target_user_ids.add(c.user_id)
    
    # Commit changes
    await db.commit()

    # Attendance Check
    if rehearsal_data.create_attendance_check:
        # 期限設定（未指定なら稽古日の24時間前）
        deadline = rehearsal_data.attendance_deadline
        if not deadline:
            deadline = rehearsal_data.date - timedelta(hours=24)
        
        # ターゲット指定がある場合はそれを使用、なければ全員（後方互換性として、Frontendがparticipantsを送ってこない場合は全員にするか？
        # いや、Frontendが古い場合、target_user_idsはDefault Staffのみになる。
        # 古い挙動は「全員」だった。
        # なので、rehearsal_data.participants/castsがNoneの場合は、target_user_ids=None (All) を渡すべき。
        # しかし、Default Staff Auto-Assignmentでtarget_user_idsに追加している。
        # ユーザーの意図としては「登録された人＝出欠確認対象」
        # 新UIからは明示的に送られる。
        # 旧UI（もしあれば）からはNoneが来る -> Default Staffのみになる -> これだと全員に飛ばない。
        # 安全策: participants/castsがNoneの場合は target_user_ids=None を渡して「全員」にする。
        # 指定がある場合は target_user_ids を渡す。
        
        attendance_targets = list(target_user_ids) if (rehearsal_data.participants is not None or rehearsal_data.casts is not None) else None

        attendance_service = AttendanceService(db, discord_service)
        # BackgroundTaskにするとコンテキストが切れる可能性があるのでawaitで実行するか、sessionを共有する必要がある。
        # ここではawaitで実行。
        # Project取得 (Explicit select to avoid potential db.get issues)
        project_result = await db.execute(select(TheaterProject).where(TheaterProject.id == schedule.project_id))
        project = project_result.scalar_one()

        # Naive conversion for AttendanceEvent (since columns are stored as naive)
        deadline_naive = deadline.replace(tzinfo=None) if deadline and deadline.tzinfo else deadline
        schedule_date_naive = rehearsal_data.date.replace(tzinfo=None) if rehearsal_data.date.tzinfo else rehearsal_data.date

        await attendance_service.create_attendance_event(
            project=project,
            title=f"稽古: {rehearsal_data.date.strftime('%m/%d %H:%M')}",
            deadline=deadline_naive,
            schedule_date=schedule_date_naive,
            location=rehearsal_data.location,
            description=rehearsal_data.notes,
            target_user_ids=attendance_targets
        )

    # Re-fetch everything to be safe and consistent with update_rehearsal
     # Re-fetch rehearsal with full options to ensure relationships are loaded for response
    result = await db.execute(
        select(Rehearsal)
        .where(Rehearsal.id == rehearsal.id)
        .options(
            selectinload(Rehearsal.participants).options(selectinload(RehearsalParticipant.user)),
            selectinload(Rehearsal.casts).options(
                selectinload(RehearsalCast.character),
                selectinload(RehearsalCast.user)
            )
        )
    )
    rehearsal = result.scalar_one()

    # Display Name Map for manual response construction (if needed)
    # But response model uses relations?
    # RehearsalResponse defines participants as list[RehearsalParticipantResponse]
    # RehearsalParticipantResponse configuration: from_attributes = True?
    # Let's check schema. RehearsalParticipantResponse uses `user_name` etc.
    # We might need manual mapping if relations are not strictly matching pydantic fields.
    
    # Old logic constructed `participants_response` manually.
    # Let's keep manual construction to be safe because of `display_name` map.
    
    member_result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == schedule.project_id)
    )
    members = member_result.scalars().all()
    display_name_map = {m.user_id: m.display_name for m in members}

    participants_response = [
        RehearsalParticipantResponse(
            user_id=p.user_id,
            user_name=p.user.discord_username,
            display_name=display_name_map.get(p.user_id),
            staff_role=p.staff_role
        ) for p in rehearsal.participants
    ]
    casts_response = [
        RehearsalCastResponse(
            character_id=c.character_id,
            character_name=c.character.name,
            user_id=c.user_id,
            user_name=c.user.discord_username,
            display_name=display_name_map.get(c.user_id),
        ) for c in rehearsal.casts
    ]

    # Webhook通知（既存機能の維持）
    project = await db.get(TheaterProject, schedule.project_id)
    scene_headings = [s.heading for s in rehearsal.scenes]
    scene_text = ", ".join(scene_headings) if scene_headings else None
    
    date_str = rehearsal.date.strftime("%Y/%m/%d %H:%M")
    content = f"📅 **稽古が追加されました**\n日時: {date_str}\n場所: {rehearsal.location or '未定'}"
    if scene_text:
        content += f"\nシーン: {scene_text}"

    # メンションの追加
    mention_ids = set()
    # Participants
    for p in rehearsal.participants:
        if p.user and p.user.discord_id:
            mention_ids.add(p.user.discord_id)
    # Casts
    for c in rehearsal.casts:
        if c.user and c.user.discord_id:
            mention_ids.add(c.user.discord_id)
    
    if mention_ids:
        mentions = " ".join([f"<@{uid}>" for uid in mention_ids])
        content += f"\n\n{mentions}"
        
    if project.discord_webhook_url:
        background_tasks.add_task(
            discord_service.send_notification,
            content=content,
            webhook_url=project.discord_webhook_url,
        )

    return RehearsalResponse(
        id=rehearsal.id,
        schedule_id=rehearsal.schedule_id,
        scene_id=rehearsal.scene_id, # Deprecated
        scene_heading=scene_text, # Join headings
        date=rehearsal.date,
        duration_minutes=rehearsal.duration_minutes,
        location=rehearsal.location,
        notes=rehearsal.notes,
        participants=participants_response,
        casts=casts_response
    )

    # 出席確認作成（オプション）
    # 出席確認作成（オプション）
    if rehearsal_data.create_attendance_check:
        # 期限設定（未指定なら稽古日の24時間前）
        deadline = rehearsal_data.attendance_deadline
        if not deadline:
            deadline = rehearsal.date - timedelta(hours=24)
        
        # プロジェクト取得
        if project and project.discord_channel_id:
            # AttendanceServiceを使用
            attendance_service = AttendanceService(db, discord_service)
            title = f"稽古出席確認: {scene_heading or '稽古'}"
            await attendance_service.create_attendance_event(
                project=project,
                title=title,
                deadline=deadline,
                schedule_date=rehearsal.date,
                location=rehearsal.location,
                description=None
            )

    return RehearsalResponse(
        id=rehearsal.id,
        schedule_id=rehearsal.schedule_id,
        scene_id=rehearsal.scene_id,
        scene_heading=scene_heading,
        date=rehearsal.date.replace(tzinfo=timezone.utc),
        duration_minutes=rehearsal.duration_minutes,
        location=rehearsal.location,
        notes=rehearsal.notes,
        participants=participants_response,
        casts=casts_response_list,
    )


@router.put("/rehearsals/{rehearsal_id}", response_model=RehearsalResponse)
async def update_rehearsal(
    rehearsal_id: UUID,
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
    
    # 複数シーン更新
    if rehearsal_data.scene_ids is not None:
        if not rehearsal_data.scene_ids:
            rehearsal.scenes = []
            rehearsal.scene_id = None # Legacy ID clear
        else:
            scenes_result = await db.execute(select(Scene).where(Scene.id.in_(rehearsal_data.scene_ids)))
            scenes = scenes_result.scalars().all()
            rehearsal.scenes = scenes
            # Legacy ID sync (first one)
            rehearsal.scene_id = scenes[0].id if scenes else None

    if rehearsal_data.date is not None:
        # Naive UTC conversion for DB
        date_naive = rehearsal_data.date.replace(tzinfo=None) if rehearsal_data.date.tzinfo else rehearsal_data.date
        rehearsal.date = date_naive
    if rehearsal_data.duration_minutes is not None:
        rehearsal.duration_minutes = rehearsal_data.duration_minutes
    if rehearsal_data.location is not None:
        rehearsal.location = rehearsal_data.location
    if rehearsal_data.notes is not None:
        rehearsal.notes = rehearsal_data.notes
        
    # 参加者更新 (全置換)
    if rehearsal_data.participants is not None:
        # 既存削除
        await db.execute(delete(RehearsalParticipant).where(RehearsalParticipant.rehearsal_id == rehearsal.id))
        # 新規追加
        for p in rehearsal_data.participants:
            db.add(RehearsalParticipant(
                rehearsal_id=rehearsal.id, 
                user_id=p.user_id, 
                staff_role=p.staff_role
            ))

    # キャスト更新 (全置換)
    if rehearsal_data.casts is not None:
        # 既存削除
        await db.execute(delete(RehearsalCast).where(RehearsalCast.rehearsal_id == rehearsal.id))
        # 新規追加
        for c in rehearsal_data.casts:
            db.add(RehearsalCast(
                rehearsal_id=rehearsal.id, 
                user_id=c.user_id, 
                character_id=c.character_id
            ))

    await db.commit()
    # Re-fetch rehearsal with full options to ensure relationships are loaded for response
    result = await db.execute(
        select(Rehearsal)
        .where(Rehearsal.id == rehearsal_id)
        .options(
            selectinload(Rehearsal.participants).options(selectinload(RehearsalParticipant.user)),
            selectinload(Rehearsal.casts).options(
                selectinload(RehearsalCast.character),
                selectinload(RehearsalCast.user)
            )
        )
    )
    rehearsal = result.scalar_one()

    # シーン情報 & キャスト構成
    scene_headings = [s.heading for s in rehearsal.scenes]
    scene_heading = ", ".join(scene_headings) if scene_headings else None
    
    casts_response_list = []
    
    rehearsal_cast_map = {c.character_id: c for c in rehearsal.casts}
    
    # Display Name Map
    member_result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == schedule.project_id)
    )
    members = member_result.scalars().all()
    display_name_map = {m.user_id: m.display_name for m in members}

    # Explicit casts
    for rc in rehearsal.casts:
        casts_response_list.append(RehearsalCastResponse(
            character_id=rc.character_id,
            character_name=rc.character.name,
            user_id=rc.user_id,
            user_name=rc.user.discord_username,
            display_name=display_name_map.get(rc.user_id)
        ))

    if rehearsal.scene_id:
        result = await db.execute(
            select(Scene)
            .where(Scene.id == rehearsal.scene_id)
            .options(
                selectinload(Scene.lines).options(
                    selectinload(Line.character).options(
                        selectinload(Character.castings).options(
                            selectinload(CharacterCasting.user)
                        )
                    )
                )
            )
        )
        scene = result.scalar_one_or_none()
        if scene:
            scene_heading = scene.heading
            
            # デフォルト配役の取得 (Missing characters only)
            unique_characters = {}
            for line in scene.lines:
                if line.character_id not in unique_characters:
                    unique_characters[line.character_id] = line.character
            
            for char_id, char in unique_characters.items():
                if char_id not in rehearsal_cast_map:
                    for casting in char.castings:
                        casts_response_list.append(RehearsalCastResponse(
                            character_id=char.id,
                            character_name=char.name,
                            user_id=casting.user_id,
                            user_name=casting.user.discord_username,
                            display_name=display_name_map.get(casting.user_id)
                        ))

    return RehearsalResponse(
        id=rehearsal.id,
        schedule_id=rehearsal.schedule_id,
        scene_id=rehearsal.scene_id,
        scene_heading=scene_heading,
        date=rehearsal.date.replace(tzinfo=timezone.utc),
        duration_minutes=rehearsal.duration_minutes,
        location=rehearsal.location,
        notes=rehearsal.notes,
        participants=[
            RehearsalParticipantResponse(
                user_id=p.user_id,
                user_name=p.user.discord_username,
                display_name=display_name_map.get(p.user_id),
                staff_role=p.staff_role
            ) for p in rehearsal.participants
        ],
        casts=casts_response_list,
    )


@router.post("/rehearsals/{rehearsal_id}/participants/{user_id}")
async def add_participant(
    rehearsal_id: UUID,
    user_id: UUID,
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

    # プロジェクトIDを取得するためのスケジュール->プロジェクト参照
    # Rehearsal -> RehearsalSchedule -> project_id
    rehearsal_schedule_query = select(RehearsalSchedule.project_id).where(RehearsalSchedule.id == rehearsal.schedule_id)
    rs_result = await db.execute(rehearsal_schedule_query)
    project_id = rs_result.scalar_one()

    # 対象ユーザーのプロジェクトメンバー情報を取得（デフォルトロールのため）
    pm_query = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    )
    pm_result = await db.execute(pm_query)
    target_member = pm_result.scalar_one_or_none()
    
    default_role = target_member.default_staff_role if target_member else None

    # 参加者追加
    participant = RehearsalParticipant(
        rehearsal_id=rehearsal_id,
        user_id=user_id,
        staff_role=default_role,
    )
    db.add(participant)
    try:
        await db.commit()
    except Exception:
        # 既に参加済みの場合は無視する (Idempotent)
        await db.rollback()

    return {"message": "参加者を追加しました"}


@router.delete("/rehearsals/{rehearsal_id}")
async def delete_rehearsal(
    rehearsal_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
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

    # Discord通知用データ退避
    rehearsal_date = rehearsal.date.strftime("%Y/%m/%d %H:%M")
    
    # 削除
    await db.delete(rehearsal)
    await db.commit()

    # Discord通知
    project = await db.get(TheaterProject, schedule.project_id)
    if project.discord_webhook_url:
        background_tasks.add_task(
            discord_service.send_notification,
            content=f"🗑️ **稽古が削除されました**\nプロジェクト: {project.name}\n日時: {rehearsal_date}",
            webhook_url=project.discord_webhook_url,
        )

    return {"message": "稽古を削除しました"}


@router.put("/rehearsals/{rehearsal_id}/participants/{user_id}")
async def update_participant_role(
    rehearsal_id: UUID,
    user_id: UUID,
    role_data: RehearsalParticipantUpdate,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """参加者の役割を更新.

    Args:
        rehearsal_id: 稽古ID
        user_id: ユーザーID
        role_data: 更新データ
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

    # 参加者情報取得
    result = await db.execute(
        select(RehearsalParticipant).where(
            RehearsalParticipant.rehearsal_id == rehearsal_id,
            RehearsalParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant is None:
        raise HTTPException(status_code=404, detail="参加者が見つかりません")

    # 稽古情報取得（権限チェック用）
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one()

    # プロジェクトID取得
    result = await db.execute(
        select(RehearsalSchedule.project_id).where(RehearsalSchedule.id == rehearsal.schedule_id)
    )
    project_id = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="変更権限がありません")

    # 更新
    participant.staff_role = role_data.staff_role
    await db.commit()

    return {"message": "役割を更新しました"}


@router.delete("/rehearsals/{rehearsal_id}/participants/{user_id}")
async def delete_participant(
    rehearsal_id: UUID,
    user_id: UUID,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """参加者を削除.

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

    # 参加者情報取得
    result = await db.execute(
        select(RehearsalParticipant).where(
            RehearsalParticipant.rehearsal_id == rehearsal_id,
            RehearsalParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant is None:
        raise HTTPException(status_code=404, detail="参加者が見つかりません")

    # 稽古情報取得（権限チェック用）
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one()

    # プロジェクトID取得
    result = await db.execute(
        select(RehearsalSchedule.project_id).where(RehearsalSchedule.id == rehearsal.schedule_id)
    )
    project_id = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="削除権限がありません")

    # 削除
    await db.delete(participant)
    await db.commit()

    return {"message": "参加者を削除しました"}


@router.post("/rehearsals/{rehearsal_id}/casts")
async def add_cast(
    rehearsal_id: UUID,
    cast_data: RehearsalCastCreate,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """稽古にキャストを割り当て.

    Args:
        rehearsal_id: 稽古ID
        cast_data: キャストデータ
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

    # プロジェクトID取得
    result = await db.execute(
        select(RehearsalSchedule.project_id).where(RehearsalSchedule.id == rehearsal.schedule_id)
    )
    project_id = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="変更権限がありません")

    # 重複チェック（既にその稽古でその役に誰かがいるか）
    result = await db.execute(
        select(RehearsalCast).where(
            RehearsalCast.rehearsal_id == rehearsal_id,
            RehearsalCast.character_id == cast_data.character_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # 上書きする（またはエラーにするが、今回は上書きしやすいように削除してから追加、あるいは更新）
        await db.delete(existing)

    # キャスト追加
    cast = RehearsalCast(
        rehearsal_id=rehearsal_id,
        character_id=cast_data.character_id,
        user_id=cast_data.user_id,
    )
    db.add(cast)
    await db.commit()

    return {"message": "キャストを割り当てました"}


@router.delete("/rehearsals/{rehearsal_id}/casts/{character_id}")
async def delete_cast(
    rehearsal_id: UUID,
    character_id: UUID,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """稽古のキャスト割り当てを解除.

    Args:
        rehearsal_id: 稽古ID
        character_id: キャラクターID
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

    # プロジェクトID取得
    result = await db.execute(
        select(RehearsalSchedule.project_id).where(RehearsalSchedule.id == rehearsal.schedule_id)
    )
    project_id = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="削除権限がありません")

    # キャスト取得
    result = await db.execute(
        select(RehearsalCast).where(
            RehearsalCast.rehearsal_id == rehearsal_id,
            RehearsalCast.character_id == character_id,
        )
    )
    cast = result.scalar_one_or_none()
    if cast is None:
        raise HTTPException(status_code=404, detail="キャスト割り当てが見つかりません")

    # 削除
    await db.delete(cast)
    await db.commit()

    return {"message": "キャスト割り当てを解除しました"}
