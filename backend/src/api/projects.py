from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog import get_logger

from src.db import get_db
from src.db.models import AuditLog, Milestone, ProjectMember, Reservation, TheaterProject, User
from src.dependencies.auth import get_current_user_dep
from src.dependencies.permissions import get_project_member_dep, get_project_owner_dep
from src.schemas.project import (
    MemberRoleUpdate,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
    ProjectCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from src.services.attendance import AttendanceService
from src.services.discord import DiscordService, get_discord_service
from src.services.project_limit import get_user_restricted_project_ids, is_project_restricted

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> ProjectResponse:
    """プロジェクトを作成.

    Args:
        project_data: プロジェクト作成データ
        background_tasks: バックグラウンドタスク
        current_user: 認証ユーザー
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        ProjectResponse: 作成されたプロジェクト

    Raises:
        HTTPException: 認証エラー
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    from src.services.project_limit import check_project_limit

    # 公開脚本からのインポート時は、強制的に非公開にする（帰属保護のため）
    if project_data.source_public_script_id:
        project_data.is_public = False

    # プロジェクト作成数制限チェック
    # 公開脚本を含むプロジェクトは除外、非公開プロジェクトは上限2つ
    await check_project_limit(current_user.id, db, new_project_is_public=project_data.is_public)

    # プロジェクトを作成
    project = TheaterProject(
        name=project_data.name,
        description=project_data.description,
        is_public=project_data.is_public,
        attendance_reminder_1_hours=project_data.attendance_reminder_1_hours,
        attendance_reminder_2_hours=project_data.attendance_reminder_2_hours,
        created_by_id=current_user.id,
    )
    db.add(project)
    await db.flush()

    # 作成者をオーナーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)

    # 監査ログ
    audit = AuditLog(
        event="project.create",
        user_id=current_user.id,
        project_id=project.id,
        details=f"Project '{project.name}' created.",
    )
    db.add(audit)

    # 公開脚本からのインポート処理
    if project_data.source_public_script_id:
        from src.db.models import Script
        from src.services.script_processor import parse_and_save_fountain

        # 公開脚本を取得
        source_script_res = await db.execute(
            select(Script).where(
                Script.id == project_data.source_public_script_id, Script.is_public == True
            )
        )
        source_script = source_script_res.scalar_one_or_none()

        if source_script:
            # 脚本をコピーして新規作成
            new_script = Script(
                project_id=project.id,
                uploaded_by=current_user.id,
                title=source_script.title,
                content=source_script.content,
                is_public=False,  # コピーしたものは一旦非公開
                revision=1,
                author=source_script.author,
            )
            db.add(new_script)
            await db.flush()

            # 監査ログ詳細更新
            audit.details += f" Imported from public script '{source_script.title}'."

            # ScriptProcessorで解析を実行（バックグラウンドではなく、同期的に実行して結果を反映させる）
            try:
                await parse_and_save_fountain(new_script, new_script.content, db)
            except Exception as e:
                logger.error(f"Failed to process imported script: {e}")
                # 失敗してもプロジェクト作成は成功とする（後でリトライ可能）
        else:
            logger.warning(
                f"Source public script not found: {project_data.source_public_script_id}"
            )

    await db.commit()
    await db.refresh(project)

    # Discord通知
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"🎉 **新しいプロジェクトが作成されました**\nプロジェクト: {project.name}\n作成者: {current_user.display_name}",
        webhook_url=project.discord_webhook_url,  # 現状はNoneだが将来的に設定可能
    )

    return await _build_project_response(project, "owner", db)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """参加中のプロジェクト一覧を取得.

    Args:
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        list[ProjectResponse]: プロジェクトリスト

    Raises:
        HTTPException: 認証エラー
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # ユーザーが参加しているプロジェクト一覧を取得
    result = await db.execute(
        select(TheaterProject, ProjectMember.role)
        .join(ProjectMember)
        .where(ProjectMember.user_id == current_user.id)
    )
    projects_with_roles = result.all()

    # 全プロジェクトの制限状態を一括計算（作成者ごとにキャッシュ）
    user_restricted_cache = {}  # user_id -> set(restricted_project_ids)

    projects_response = []
    for project, role in projects_with_roles:
        if project.is_public:
            is_restricted = False
        elif not project.created_by_id:
            is_restricted = False
        else:
            if project.created_by_id not in user_restricted_cache:
                user_restricted_cache[
                    project.created_by_id
                ] = await get_user_restricted_project_ids(project.created_by_id, db)
            is_restricted = project.id in user_restricted_cache[project.created_by_id]

        projects_response.append(
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                discord_webhook_url=project.discord_webhook_url,
                discord_script_webhook_url=project.discord_script_webhook_url,
                discord_channel_id=project.discord_channel_id,
                is_public=project.is_public,
                attendance_reminder_1_hours=project.attendance_reminder_1_hours,
                attendance_reminder_2_hours=project.attendance_reminder_2_hours,
                is_restricted=is_restricted,
                created_at=project.created_at,
                role=role,
            )
        )

    return projects_response


async def _build_project_response(
    project: TheaterProject, role: str, db: AsyncSession
) -> ProjectResponse:
    """プロジェクトレスポンスを構築するヘルパー関数."""
    is_restricted = await is_project_restricted(project.id, db)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        discord_webhook_url=project.discord_webhook_url,
        discord_script_webhook_url=project.discord_script_webhook_url,
        discord_channel_id=project.discord_channel_id,
        is_public=project.is_public,
        attendance_reminder_1_hours=project.attendance_reminder_1_hours,
        attendance_reminder_2_hours=project.attendance_reminder_2_hours,
        is_restricted=is_restricted,
        created_at=project.created_at,
        role=role,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """プロジェクト詳細を取得.

    Args:
        project_id: プロジェクトID
        current_member: 現在のメンバー情報（権限チェック済み）
        db: データベースセッション

    Returns:
        ProjectResponse: プロジェクト詳細
    """
    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    return await _build_project_response(project, current_member.role, db)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_member: ProjectMember = Depends(get_project_owner_dep),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """プロジェクト情報を更新 (オーナーのみ).

    Args:
        project_id: プロジェクトID
        project_update: 更新データ
        current_member: 実行者（オーナー）
        db: データベースセッション

    Returns:
        ProjectResponse: 更新後のプロジェクト情報
    """
    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # 更新
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.discord_webhook_url is not None:
        if project_update.discord_webhook_url == "":
            project.discord_webhook_url = None
        else:
            project.discord_webhook_url = project_update.discord_webhook_url
    if project_update.discord_script_webhook_url is not None:
        if project_update.discord_script_webhook_url == "":
            project.discord_script_webhook_url = None
        else:
            project.discord_script_webhook_url = project_update.discord_script_webhook_url
    if project_update.discord_channel_id is not None:
        if project_update.discord_channel_id == "":
            project.discord_channel_id = None
        else:
            project.discord_channel_id = project_update.discord_channel_id
    if project_update.attendance_reminder_1_hours is not None:
        project.attendance_reminder_1_hours = project_update.attendance_reminder_1_hours
    if project_update.attendance_reminder_2_hours is not None:
        project.attendance_reminder_2_hours = project_update.attendance_reminder_2_hours

    # 監査ログ
    audit = AuditLog(
        event="project.update",
        user_id=current_member.user_id,
        project_id=project.id,
        details=f"Project updated. Name: {project.name}, Webhook: {'Set' if project.discord_webhook_url else 'Unset'}",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(project)

    return await _build_project_response(project, current_member.role, db)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectMemberResponse]:
    """プロジェクトメンバー一覧を取得.

    Args:
        project_id: プロジェクトID
        current_member: 現在のメンバー情報（権限チェック済み）
        db: データベースセッション

    Returns:
        list[ProjectMemberResponse]: メンバーリスト
    """
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
    )
    members = result.all()

    response = []
    for pm, user in members:
        response.append(
            ProjectMemberResponse(
                user_id=user.id,
                discord_username=user.display_name,
                role=pm.role,
                default_staff_role=pm.default_staff_role,
                display_name=pm.display_name,
                discord_avatar_url=user.discord_avatar_url,
                joined_at=pm.joined_at,
            )
        )

    return response


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: UUID,
    user_id: UUID,
    role_update: MemberRoleUpdate,
    background_tasks: BackgroundTasks,
    owner_member: ProjectMember = Depends(get_project_owner_dep),  # オーナーのみ
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> ProjectMemberResponse:
    """メンバーのロールを更新 (オーナーのみ).

    Args:
        project_id: プロジェクトID
        user_id: 対象ユーザーID
        role_update: 更新データ
        background_tasks: バックグラウンドタスク
        owner_member: 実行者（オーナー）
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        ProjectMemberResponse: 更新後のメンバー情報
    """
    # 自分自身の場合、ロールの変更（降格・委譲）は別途慎重に行う必要があるため、
    # ここでは「ロールが変わらない場合」のみ許可する（表示名などの更新用）
    if user_id == owner_member.user_id:
        if role_update.role != owner_member.role:
            raise HTTPException(status_code=400, detail="自分自身のロールは変更できません")
        # roleが同じなら続行（display_name等の更新は許可）

    # 対象メンバー取得
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
    )
    target_member = result.scalar_one_or_none()

    if target_member is None:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")

    # 更新
    old_role = target_member.role
    target_member.role = role_update.role
    if role_update.default_staff_role is not None:
        target_member.default_staff_role = role_update.default_staff_role
    if role_update.display_name is not None:
        target_member.display_name = role_update.display_name

    # User情報取得用
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()

    # 監査ログ
    audit = AuditLog(
        event="member.update_role",
        user_id=owner_member.user_id,
        project_id=project_id,
        details=f"User {user.display_name} role changed from {old_role} to {role_update.role}. Staff role: {role_update.default_staff_role}. Display name: {role_update.display_name}",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(target_member)

    # Discord通知
    # Project取得 (webhook_urlのため)
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"👮 **メンバー権限が変更されました**\nプロジェクト: {project.name}\nメンバー: {user.display_name}\n変更: {old_role} -> {role_update.role}",
        webhook_url=project.discord_webhook_url,
    )

    return ProjectMemberResponse(
        user_id=user.id,
        discord_username=user.display_name,
        role=target_member.role,
        default_staff_role=target_member.default_staff_role,
        display_name=target_member.display_name,
        discord_avatar_url=user.discord_avatar_url,
        joined_at=target_member.joined_at,
    )


@router.delete("/{project_id}/members/{user_id}")
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    background_tasks: BackgroundTasks,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> dict[str, str]:
    """メンバーを削除 (オーナーまたは本人).

    Args:
        project_id: プロジェクトID
        user_id: 対象ユーザーID
        background_tasks: バックグラウンドタスク
        current_member: 実行者
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        dict: メッセージ
    """
    # 権限チェック: オーナー または 本人
    is_owner = current_member.role == "owner"
    is_self = current_member.user_id == user_id

    if not (is_owner or is_self):
        raise HTTPException(status_code=403, detail="権限がありません")

    # オーナーが自分自身を削除（脱退）しようとする場合
    if is_owner and is_self:
        # 他にオーナーがいるか確認すべきだが、今回は簡易的に不可とするか、あるいはプロジェクト削除を促す
        # ここでは「オーナーは脱退不可」とする
        raise HTTPException(
            status_code=400,
            detail="オーナーは脱退できません。プロジェクトを削除するか、オーナー権限を委譲してください",
        )

    # 対象メンバー取得
    target_member = None
    if is_self:
        target_member = current_member
    else:
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
        )
        target_member = result.scalar_one_or_none()

    if target_member is None:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")

    # ユーザー名取得（通知用）
    user_name = "Unknown"
    result = await db.execute(select(User).where(User.id == user_id))
    user_res = result.scalar_one_or_none()
    if user_res:
        user_name = user_res.display_name

    # 削除
    await db.delete(target_member)

    # 監査ログ
    audit = AuditLog(
        event="member.remove",
        user_id=current_member.user_id,
        project_id=project_id,
        details=f"User {user_name} removed from project.",
    )
    db.add(audit)

    await db.commit()

    # Discord通知
    project = await db.get(TheaterProject, project_id)
    action_text = "脱退しました" if is_self else "削除されました"
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"👋 **メンバーが{action_text}**\nプロジェクト: {project.name}\nユーザー: {user_name}",
        webhook_url=project.discord_webhook_url,
    )

    return {"message": "メンバーを削除しました"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    current_member: ProjectMember = Depends(get_project_owner_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> dict[str, str]:
    """プロジェクトを削除 (オーナーのみ).

    Args:
        project_id: プロジェクトID
        background_tasks: バックグラウンドタスク
        current_member: 実行者（オーナー）
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        dict: メッセージ
    """
    # プロジェクト取得
    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # Discord通知のための情報を保存
    project_name = project.name
    webhook_url = project.discord_webhook_url
    owner_username = current_member.user.display_name

    # 削除 (cascadeにより関連データも削除されるはず)
    await db.delete(project)

    # 注: プロジェクト削除に伴い、AuditLogも削除される設定にしているため、
    # データベース上には痕跡が残らない。

    await db.commit()

    # Discord通知
    if webhook_url:
        background_tasks.add_task(
            discord_service.send_notification,
            content=f"🗑️ **プロジェクトが削除されました**\nプロジェクト: {project_name}\n実行者: {owner_username}",
            webhook_url=webhook_url,
        )

    return {"message": "プロジェクトを削除しました"}


@router.post("/{project_id}/milestones", response_model=MilestoneResponse)
async def create_milestone(
    project_id: UUID,
    milestone_data: MilestoneCreate,
    background_tasks: BackgroundTasks,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> MilestoneResponse:
    """マイルストーンを作成."""
    logger.info(f"Create Milestone Request: {milestone_data.model_dump()}")

    if current_member.role == "viewer":
        raise HTTPException(status_code=403, detail="権限がありません")

    # Timezone handling: DB expects naive UTC
    start_date = milestone_data.start_date
    if start_date.tzinfo:
        start_date = start_date.astimezone(UTC).replace(tzinfo=None)

    end_date = milestone_data.end_date
    if end_date and end_date.tzinfo:
        end_date = end_date.astimezone(UTC).replace(tzinfo=None)

    milestone = Milestone(
        project_id=project_id,
        title=milestone_data.title,
        start_date=start_date,
        end_date=end_date,
        location=milestone_data.location,
        color=milestone_data.color,
        reservation_capacity=milestone_data.reservation_capacity,
        is_public=milestone_data.is_public,  # 🆕 公開設定
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)

    # 出席確認作成（オプション）
    # 出席確認作成（オプション）
    logger.info(f"Attendance check request: {milestone_data.create_attendance_check}")
    if milestone_data.create_attendance_check:
        project = await db.get(TheaterProject, project_id)
        if project:
            logger.info(f"Project found: {project.name}, Channel ID: {project.discord_channel_id}")
            if project.discord_channel_id:
                # 期限設定（未指定なら開始日時の24時間前）
                deadline = milestone_data.attendance_deadline
                if not deadline:
                    from datetime import timedelta

                    deadline = milestone.start_date - timedelta(hours=24)

                attendance_service = AttendanceService(db, discord_service)
                title = f"イベント出席確認: {milestone.title}"
                result = await attendance_service.create_attendance_event(
                    project=project,
                    title=title,
                    deadline=deadline,
                    schedule_date=milestone.start_date,
                    location=milestone.location,
                    description=milestone.description,
                )
                logger.info(f"Attendance service result: {result}")
            else:
                logger.warning("Discord Channel ID is missing")
        else:
            logger.warning("Project not found")

    # Discord通知 (Webhook)
    project = await db.get(TheaterProject, project_id)
    if project.discord_webhook_url:
        # Discord Timestamp format (Date only)
        start_ts = int(milestone.start_date.replace(tzinfo=UTC).timestamp())
        date_str = f"<t:{start_ts}:d>"
        if milestone.end_date:
            end_ts = int(milestone.end_date.replace(tzinfo=UTC).timestamp())
            date_str += f" - <t:{end_ts}:d>"

        background_tasks.add_task(
            discord_service.send_notification,
            content=f"📅 **新しいマイルストーンが作成されました**\nプロジェクト: {project.name}\nタイトル: {milestone.title}\n日程: {date_str}\n場所: {milestone.location or '未定'}\n詳細: {milestone.description or 'なし'}",
            webhook_url=project.discord_webhook_url,
        )

    return MilestoneResponse(
        id=milestone.id,
        project_id=milestone.project_id,
        title=milestone.title,
        start_date=milestone.start_date,
        end_date=milestone.end_date,
        description=milestone.description,
        location=milestone.location,
        color=milestone.color,
    )


@router.get("/{project_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(
    project_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> list[MilestoneResponse]:
    """マイルストーン一覧を取得."""
    # 予約数も取得するためにGroup Byする
    # Reservationテーブルからのsum(count)を取得
    stmt = (
        select(Milestone, func.coalesce(func.sum(Reservation.count), 0).label("total_reserved"))
        .outerjoin(Reservation, Milestone.id == Reservation.milestone_id)
        .where(Milestone.project_id == project_id)
        .group_by(Milestone.id)
        .order_by(Milestone.start_date)
    )
    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for milestone, total_reserved in rows:
        m_response = MilestoneResponse.model_validate(milestone)
        m_response.current_reservation_count = total_reserved
        response.append(m_response)

    return response

    return response


@router.patch("/{project_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    project_id: UUID,
    milestone_id: UUID,
    milestone_update: MilestoneUpdate,
    background_tasks: BackgroundTasks,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> MilestoneResponse:
    """マイルストーンを更新."""
    if current_member.role == "viewer":
        raise HTTPException(status_code=403, detail="権限がありません")

    stmt = select(Milestone).where(Milestone.id == milestone_id, Milestone.project_id == project_id)
    result = await db.execute(stmt)
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=404, detail="マイルストーンが見つかりません")

    # 更新
    if milestone_update.title is not None:
        milestone.title = milestone_update.title
    if milestone_update.start_date is not None:
        # Timezone check
        sd = milestone_update.start_date
        if sd.tzinfo:
            sd = sd.astimezone(UTC).replace(tzinfo=None)
        milestone.start_date = sd
    if milestone_update.end_date is not None:
        ed = milestone_update.end_date
        if ed.tzinfo:
            ed = ed.astimezone(UTC).replace(tzinfo=None)
        milestone.end_date = ed
    if milestone_update.description is not None:
        milestone.description = milestone_update.description
    if milestone_update.location is not None:
        milestone.location = milestone_update.location
    if milestone_update.color is not None:
        milestone.color = milestone_update.color
    if milestone_update.reservation_capacity is not None:
        milestone.reservation_capacity = milestone_update.reservation_capacity
    if milestone_update.is_public is not None:  # 🆕 公開設定
        milestone.is_public = milestone_update.is_public

    await db.commit()
    await db.refresh(milestone)

    # 現在の予約数を再計算
    count_stmt = select(func.sum(Reservation.count)).where(Reservation.milestone_id == milestone.id)
    count_res = await db.scalar(count_stmt)
    current_count = count_res or 0

    response = MilestoneResponse.model_validate(milestone)
    response.current_reservation_count = current_count

    return response


@router.delete("/{project_id}/milestones/{milestone_id}", status_code=204)
async def delete_milestone(
    project_id: UUID,
    milestone_id: UUID,
    background_tasks: BackgroundTasks,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> None:
    """マイルストーンを削除."""
    if current_member.role == "viewer":
        raise HTTPException(status_code=403, detail="権限がありません")

    stmt = select(Milestone).where(Milestone.id == milestone_id, Milestone.project_id == project_id)
    result = await db.execute(stmt)
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=404, detail="マイルストーンが見つかりません")

    # Discord通知用データ退避
    milestone_title = milestone.title

    await db.delete(milestone)
    await db.commit()

    # Discord通知
    project = await db.get(TheaterProject, project_id)
    if project.discord_webhook_url:
        background_tasks.add_task(
            discord_service.send_notification,
            content=f"🗑️ **マイルストーンが削除されました**\nプロジェクト: {project.name}\nタイトル: {milestone_title}",
            webhook_url=project.discord_webhook_url,
        )


@router.post("/import-script/{script_id}", response_model=ProjectResponse)
async def import_script(
    script_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> ProjectResponse:
    """公開スクリプトからプロジェクトを作成（インポート）.

    Args:
        script_id: 元となる公開スクリプトID
        background_tasks: バックグラウンドタスク
        current_user: 認証ユーザー
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        ProjectResponse: 作成されたプロジェクト

    Raises:
        HTTPException: プロジェクト作成上限、脚本非公開等
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    from src.services.project_limit import check_project_limit

    # 1. プロジェクト作成数制限チェック
    # 公開脚本からのインポートは「帰属保護のため非公開」として作成するため、制限対象
    await check_project_limit(current_user.id, db, new_project_is_public=False)

    # 2. 脚本取得（公開チェック）
    from src.db.models import (
        Character,
        Line,
        Scene,
        SceneCharacterMapping,
        SceneChart,
        Script,
    )

    source_script = await db.get(Script, script_id)
    if not source_script:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    if not source_script.is_public:
        raise HTTPException(status_code=403, detail="この脚本は公開されていません")

    # 元のプロジェクト名などを参照
    source_project = await db.get(TheaterProject, source_script.project_id)
    new_project_name = f"{source_project.name} (Copy)" if source_project else "Imported Project"

    # 3. 新規プロジェクト作成
    new_project = TheaterProject(
        name=new_project_name,
        description=f"Imported from script: {source_script.title}",
        is_public=False,  # 帰属保護のため非公開として作成
        created_by_id=current_user.id,
    )
    db.add(new_project)
    await db.flush()

    # オーナー追加
    member = ProjectMember(
        project_id=new_project.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)

    # 4. 脚本データのコピー
    # Script
    new_script = Script(
        project_id=new_project.id,
        uploaded_by=current_user.id,
        title=source_script.title,
        content=source_script.content,
        is_public=False,  # インポート元が公開でも、コピーは非公開
        author=source_script.author,
    )
    db.add(new_script)
    await db.flush()

    # 関連データのコピー（Characters, Scenes, Lines, SceneChart）
    # 元データを全ロードする必要があるため、少し重いがEager Loadingする

    # Characters
    char_map = {}  # old_id -> new_instance
    stmt_char = select(Character).where(Character.script_id == source_script.id)
    res_char = await db.execute(stmt_char)
    source_chars = res_char.scalars().all()

    for sc in source_chars:
        nc = Character(script_id=new_script.id, name=sc.name, description=sc.description)
        db.add(nc)
        await db.flush()
        char_map[sc.id] = nc

    # Scenes & Lines
    stmt_scene = (
        select(Scene)
        .where(Scene.script_id == source_script.id)
        .options(selectinload(Scene.lines))
        .order_by(Scene.act_number, Scene.scene_number)
    )
    res_scene = await db.execute(stmt_scene)
    source_scenes = res_scene.scalars().all()

    scene_map = {}  # old_id -> new_instance

    for ss in source_scenes:
        ns = Scene(
            script_id=new_script.id,
            act_number=ss.act_number,
            scene_number=ss.scene_number,
            heading=ss.heading,
            description=ss.description,
        )
        db.add(ns)
        await db.flush()
        scene_map[ss.id] = ns

        # Lines
        for sl in ss.lines:
            nl = Line(
                scene_id=ns.id,
                character_id=char_map[sl.character_id].id
                if sl.character_id and sl.character_id in char_map
                else None,
                content=sl.content,
                order=sl.order,
            )
            db.add(nl)

    # SceneChart (もしあれば)
    stmt_chart = (
        select(SceneChart)
        .where(SceneChart.script_id == source_script.id)
        .options(selectinload(SceneChart.mappings))
    )
    res_chart = await db.execute(stmt_chart)
    source_chart = res_chart.scalar_one_or_none()

    if source_chart:
        new_chart = SceneChart(script_id=new_script.id)
        db.add(new_chart)
        await db.flush()

        for sm in source_chart.mappings:
            if sm.scene_id in scene_map and sm.character_id in char_map:
                nm = SceneCharacterMapping(
                    chart_id=new_chart.id,
                    scene_id=scene_map[sm.scene_id].id,
                    character_id=char_map[sm.character_id].id,
                )
                db.add(nm)

    # 監査ログ
    audit = AuditLog(
        event="project.import_script",
        user_id=current_user.id,
        project_id=new_project.id,
        details=f"Project imported from public script '{source_script.title}' (ID: {source_script.id})",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_project)

    # Discord通知（必要であれば）
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"📥 **脚本がインポートされました**\n新プロジェクト: {new_project.name}\nユーザー: {current_user.display_name}\n元脚本: {source_script.title}",
        webhook_url=new_project.discord_webhook_url,  # 現在はNone
    )

    return ProjectResponse(
        id=new_project.id,
        name=new_project.name,
        description=new_project.description,
        discord_webhook_url=new_project.discord_webhook_url,
        discord_script_webhook_url=new_project.discord_script_webhook_url,
        created_at=new_project.created_at,
        role="owner",
    )
