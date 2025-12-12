from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from src.db import get_db
from src.db.models import AuditLog, ProjectMember, TheaterProject, User, Milestone
from src.dependencies.auth import get_current_user_dep
from src.dependencies.permissions import get_project_member_dep, get_project_owner_dep
from src.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectMemberResponse,
    ProjectUpdate,
    MemberRoleUpdate,
    MilestoneCreate,
    MilestoneResponse,
)
from src.services.discord import DiscordService, get_discord_service
from src.services.attendance import AttendanceService

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

    # プロジェクトを作成
    project = TheaterProject(
        name=project_data.name,
        description=project_data.description,
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

    await db.commit()
    await db.refresh(project)

    # Discord通知
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"🎉 **新しいプロジェクトが作成されました**\nプロジェクト: {project.name}\n作成者: {current_user.discord_username}",
        webhook_url=project.discord_webhook_url, # 現状はNoneだが将来的に設定可能
    )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        discord_webhook_url=project.discord_webhook_url,
        discord_script_webhook_url=project.discord_script_webhook_url,
        created_at=project.created_at,
        role="owner"
    )


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
    
    projects_response = []
    for project, role in result.all():
        projects_response.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            discord_webhook_url=project.discord_webhook_url,
            discord_script_webhook_url=project.discord_script_webhook_url,
            created_at=project.created_at,
            role=role
        ))

    return projects_response


def _build_project_response(project: TheaterProject, role: str) -> ProjectResponse:
    """プロジェクトレスポンスを構築するヘルパー関数."""
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        discord_webhook_url=project.discord_webhook_url,
        discord_script_webhook_url=project.discord_script_webhook_url,
        discord_channel_id=project.discord_channel_id,
        created_at=project.created_at,
        role=role
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
    
    return _build_project_response(project, current_member.role)


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

    return _build_project_response(project, current_member.role)



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
        response.append(ProjectMemberResponse(
            user_id=user.id,
            discord_username=user.discord_username,
            role=pm.role,
            default_staff_role=pm.default_staff_role,
            display_name=pm.display_name,
            discord_avatar_url=user.discord_avatar_url,
            joined_at=pm.joined_at,
        ))
    
    return response


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: UUID,
    user_id: UUID,
    role_update: MemberRoleUpdate,
    background_tasks: BackgroundTasks,
    owner_member: ProjectMember = Depends(get_project_owner_dep), # オーナーのみ
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
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
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
        details=f"User {user.discord_username} role changed from {old_role} to {role_update.role}. Staff role: {role_update.default_staff_role}. Display name: {role_update.display_name}",
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(target_member)
    
    # Discord通知
    # Project取得 (webhook_urlのため)
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"👮 **メンバー権限が変更されました**\nプロジェクト: {project.name}\nメンバー: {user.discord_username}\n変更: {old_role} -> {role_update.role}",
        webhook_url=project.discord_webhook_url,
    )
    
    return ProjectMemberResponse(
        user_id=user.id,
        discord_username=user.discord_username,
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
        raise HTTPException(status_code=400, detail="オーナーは脱退できません。プロジェクトを削除するか、オーナー権限を委譲してください")

    # 対象メンバー取得
    target_member = None
    if is_self:
        target_member = current_member
    else:
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
        target_member = result.scalar_one_or_none()
        
    if target_member is None:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")
    
    # ユーザー名取得（通知用）
    user_name = "Unknown"
    result = await db.execute(select(User.discord_username).where(User.id == user_id))
    user_name_res = result.scalar_one_or_none()
    if user_name_res:
        user_name = user_name_res

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
    owner_username = current_member.user.discord_username

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
        start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
        
    end_date = milestone_data.end_date
    if end_date and end_date.tzinfo:
        end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)

    milestone = Milestone(
        project_id=project_id,
        title=milestone_data.title,
        start_date=start_date,
        end_date=end_date,
        location=milestone_data.location,
        color=milestone_data.color,
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
                    description=milestone.description
                )
                logger.info(f"Attendance service result: {result}")
            else:
                logger.warning("Discord Channel ID is missing")
        else:
            logger.warning("Project not found")

    # Discord通知 (Webhook)
    project = await db.get(TheaterProject, project_id)
    if project.discord_webhook_url:
        date_str = milestone.start_date.strftime("%Y/%m/%d")
        if milestone.end_date:
            date_str += f" - {milestone.end_date.strftime('%Y/%m/%d')}"
        
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
    stmt = select(Milestone).where(Milestone.project_id == project_id).order_by(Milestone.start_date)
    result = await db.execute(stmt)
    milestones = result.scalars().all()
    
    return [MilestoneResponse.model_validate(m) for m in milestones]


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
