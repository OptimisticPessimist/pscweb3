"""権限チェック依存関係ロジック."""

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.db.models import ProjectMember, User
from src.dependencies.auth import get_current_user_dep


async def get_project_member_dep(
    project_id: int,
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
