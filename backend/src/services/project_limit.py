from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from src.db.models import ProjectMember, TheaterProject, User
from src.config import settings
from src.services.premium_config import PremiumConfigService

async def get_user_project_limit(user: User) -> int:
    """ユーザーの現在のプロジェクト作成上限数を取得する."""
    if user.premium_password:
        # ティアごとのパスワードと上限をチェック
        for tier in ["test", "tier2", "tier1"]:
            pw, limit = await PremiumConfigService.get_limit_and_password(tier)
            if pw and user.premium_password == pw:
                return limit
    
    return await PremiumConfigService.get_default_limit()

async def get_user_restricted_project_ids(user_id: UUID, db: AsyncSession) -> set[UUID]:
    """ユーザーが『枠主（作成者）』である非公開プロジェクトの中で、制限されているIDセットを取得する."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return set()

    limit = await get_user_project_limit(user)

    # ユーザーが「枠主」の非公開プロジェクトを古い順に取得
    stmt = (
        select(TheaterProject.id)
        .where(
            TheaterProject.created_by_id == user_id,
            TheaterProject.is_public == False
        )
        .order_by(TheaterProject.created_at.asc())
    )
    result = await db.execute(stmt)
    project_ids = [row[0] for row in result.all()]

    if len(project_ids) <= limit:
        return set()
    
    return set(project_ids[limit:])

async def is_project_restricted(
    project_id: UUID,
    db: AsyncSession
) -> bool:
    """指定したプロジェクトが作成上限超過により制限モード（閲覧のみ）になっているか判定する.
    
    プロジェクトの『枠主（作成者）』のプラン上限に基づいて判定します（他オーナーの枠は消費しない）。
    """
    project = await db.get(TheaterProject, project_id)
    if not project or project.is_public:
        return False
    
    if not project.created_by_id:
        return False # 枠主不明の場合は制限なし

    restricted_ids = await get_user_restricted_project_ids(project.created_by_id, db)
    return project.id in restricted_ids

async def check_project_limit(
    user_id: UUID, 
    db: AsyncSession, 
    project_id_to_exclude: UUID | None = None,
    new_project_is_public: bool = False
) -> None:
    """新規作成時のプロジェクト作成数（枠）制限をチェックする."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    limit = await get_user_project_limit(user)

    # 自身が「枠主（作成者）」である非公開プロジェクトの数を取得
    stmt = (
        select(TheaterProject.id)
        .where(
            TheaterProject.created_by_id == user_id,
            TheaterProject.is_public == False
        )
    )
    result = await db.execute(stmt)
    owned_private_project_ids = [row[0] for row in result.all()]
    
    current_count = len(owned_private_project_ids)

    # 現在判定中のプロジェクトが既に枠消費としてカウントされている場合は除外
    if project_id_to_exclude and project_id_to_exclude in owned_private_project_ids:
        current_count -= 1
            
    # 追加分（新規作成時）
    if not new_project_is_public:
        current_count += 1
    
    if current_count > limit:
        raise HTTPException(
            status_code=400, 
            detail=f"非公開プロジェクトの作成枠（{limit}つ）に達しています。新しいプロジェクトを作成するには、既存のプロジェクトを公開・削除するか、今月の有効なパスワードを登録して上限を増やしてください。"
        )
