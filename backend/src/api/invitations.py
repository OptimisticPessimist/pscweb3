import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import ProjectInvitation, ProjectMember, TheaterProject, User
from src.dependencies.auth import get_current_user_dep
from src.schemas.invitation import InvitationAcceptResponse, InvitationCreate, InvitationResponse
from src.services.discord import DiscordService, get_discord_service

router = APIRouter()

from uuid import UUID


@router.get("/projects/{project_id}/invitations", response_model=list[InvitationResponse])
async def list_project_invitations(
    project_id: UUID,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """プロジェクトの有効な招待リンク一覧を取得する（管理者のみ）。"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 権限チェック
    query_member = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    result_member = await db.execute(query_member)
    member = result_member.scalar_one_or_none()

    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="権限がありません")

    now = datetime.now(UTC)

    # 有効な招待状のみ取得
    # 1. 期限切れでない
    # 2. 使用回数が上限に達していない
    query = (
        select(ProjectInvitation)
        .options(selectinload(ProjectInvitation.project), selectinload(ProjectInvitation.creator))
        .where(ProjectInvitation.project_id == project_id, ProjectInvitation.expires_at > now)
    )

    result = await db.execute(query)
    invitations = result.scalars().all()

    # 使用回数上限のフィルタリング
    active_invitations = [
        inv for inv in invitations if inv.max_uses is None or inv.used_count < inv.max_uses
    ]

    return [
        InvitationResponse(
            token=inv.token,
            project_id=inv.project.id,
            project_name=inv.project.name,
            created_by=inv.creator.display_name,
            expires_at=inv.expires_at,
            max_uses=inv.max_uses,
            used_count=inv.used_count,
        )
        for inv in active_invitations
    ]


@router.post("/projects/{project_id}/invitations", response_model=InvitationResponse)
async def create_invitation(
    project_id: UUID,
    invitation_in: InvitationCreate,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """招待リンクを作成する（管理者のみ）。"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 権限チェック
    query = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="権限がありません")

    # プロジェクト情報取得
    project = await db.get(TheaterProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # トークン生成
    token_str = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=invitation_in.expires_in_hours)

    invitation = ProjectInvitation(
        project_id=project_id,
        created_by=current_user.id,
        token=token_str,
        expires_at=expires_at,
        max_uses=invitation_in.max_uses,
        used_count=0,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        token=invitation.token,
        project_id=project.id,
        project_name=project.name,
        created_by=current_user.display_name,
        expires_at=invitation.expires_at,
        max_uses=invitation.max_uses,
        used_count=invitation.used_count,
    )


@router.get("/invitations/{token}", response_model=InvitationResponse)
async def get_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """招待情報を取得する（ログイン不要）。"""
    query = (
        select(ProjectInvitation)
        .options(selectinload(ProjectInvitation.project), selectinload(ProjectInvitation.creator))
        .where(ProjectInvitation.token == token)
    )
    result = await db.execute(query)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="招待リンクが無効です")

    now = datetime.now(UTC)
    if invitation.expires_at < now:
        raise HTTPException(status_code=410, detail="招待リンクの有効期限が切れています")

    if invitation.max_uses is not None and invitation.used_count >= invitation.max_uses:
        raise HTTPException(status_code=410, detail="招待リンクの使用回数が上限に達しました")

    return InvitationResponse(
        token=invitation.token,
        project_id=invitation.project.id,
        project_name=invitation.project.name,
        created_by=invitation.creator.display_name,
        expires_at=invitation.expires_at,
        max_uses=invitation.max_uses,
        used_count=invitation.used_count,
    )


@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    token: str,
    background_tasks: BackgroundTasks,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
):
    """招待を受諾してプロジェクトに参加する。"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")

    query = select(ProjectInvitation).where(ProjectInvitation.token == token).with_for_update()
    result = await db.execute(query)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="招待リンクが無効です")

    # バリデーション
    now = datetime.now(UTC)
    if invitation.expires_at < now:
        raise HTTPException(status_code=410, detail="招待リンクの有効期限が切れています")
    if invitation.max_uses is not None and invitation.used_count >= invitation.max_uses:
        raise HTTPException(status_code=410, detail="招待リンクの使用回数が上限に達しました")

    # 既に参加済みかチェック
    query_member = select(ProjectMember).where(
        ProjectMember.project_id == invitation.project_id, ProjectMember.user_id == current_user.id
    )
    result_member = await db.execute(query_member)
    if result_member.scalar_one_or_none():
        project = await db.get(TheaterProject, invitation.project_id)
        return InvitationAcceptResponse(
            project_id=invitation.project_id, project_name=project.name, message="既に参加済みです"
        )

    # プロジェクト名取得
    project = await db.get(TheaterProject, invitation.project_id)

    # メンバー追加
    new_member = ProjectMember(
        project_id=invitation.project_id, user_id=current_user.id, role="viewer"
    )
    db.add(new_member)

    # カウント更新
    invitation.used_count += 1

    await db.commit()

    # Discord通知
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"👋 **新しいメンバーが参加しました**\nプロジェクト: {project.name}\nユーザー: {current_user.display_name}",
        webhook_url=project.discord_webhook_url,
    )

    return InvitationAcceptResponse(
        project_id=project.id, project_name=project.name, message="プロジェクトに参加しました"
    )


@router.delete("/invitations/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    token: str,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """招待リンクを削除する（本人または管理者のみ）。"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")

    query = select(ProjectInvitation).where(ProjectInvitation.token == token)
    result = await db.execute(query)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="招待リンクが見つかりません")

    # 権限チェック
    # 1. 作成者本人か
    is_creator = invitation.created_by == current_user.id

    # 2. プロジェクトの管理者か
    is_admin = False
    if not is_creator:
        query_member = select(ProjectMember).where(
            ProjectMember.project_id == invitation.project_id,
            ProjectMember.user_id == current_user.id,
        )
        result_member = await db.execute(query_member)
        member = result_member.scalar_one_or_none()
        if member and member.role in ["owner", "admin"]:
            is_admin = True

    if not is_creator and not is_admin:
        raise HTTPException(status_code=403, detail="権限がありません")

    await db.delete(invitation)
    await db.commit()

    return None
