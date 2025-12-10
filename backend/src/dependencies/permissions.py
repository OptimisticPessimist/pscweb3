"""権限チェック依存関係ロジック."""

from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import Character, Line, ProjectMember, Scene, Script, User
from src.dependencies.auth import get_current_user_dep


async def get_project_member_dep(
    project_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> ProjectMember:
    """プロジェクトメンバー情報を取得する依存関係.
    
    Args:
        project_id: プロジェクトID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        ProjectMember: プロジェクトメンバー情報

    Raises:
        HTTPException: 401 認証エラー, 403 権限エラー
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    return member


def check_role(required_roles: list[str]) -> callable:
    """指定されたロールを持つかチェックする依存関係ジェネレータ.

    Args:
        required_roles: 許可するロールのリスト (e.g. ["owner", "editor"])

    Returns:
        Callable: 依存関係関数
    """
    async def dependency(
        member: ProjectMember = Depends(get_project_member_dep)
    ) -> ProjectMember:
        if member.role not in required_roles:
            raise HTTPException(status_code=403, detail="この操作を行う権限がありません")
        return member

    return dependency


async def get_project_owner_dep(
    member: ProjectMember = Depends(get_project_member_dep)
) -> ProjectMember:
    """オーナー権限チェック用依存関係."""
    if member.role != "owner":
        raise HTTPException(status_code=403, detail="オーナー権限が必要です")
    return member


async def get_project_editor_dep(
    member: ProjectMember = Depends(get_project_member_dep)
) -> ProjectMember:
    """編集者以上（オーナーまたはエディター）権限チェック用依存関係."""
    if member.role not in ["owner", "editor"]:
        raise HTTPException(status_code=403, detail="編集権限が必要です")
    return member



async def get_script_member_dep(
    script_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> tuple[ProjectMember, Script]:
    """脚本IDからアクセス権を確認し、メンバー情報と脚本を返す.

    Args:
        script_id: 脚本ID (Path parameter)
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        tuple[ProjectMember, Script]: メンバー情報と脚本
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(
        select(Script)
        .options(
            selectinload(Script.characters).options(selectinload(Character.castings)),
            selectinload(Script.scenes)
            .selectinload(Scene.lines)
            .selectinload(Line.character)
            .selectinload(Character.castings)
        )
        .where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()

    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # 権限チェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    return member, script
