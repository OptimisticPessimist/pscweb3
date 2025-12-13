from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from src.db.models import ProjectMember, TheaterProject, Script

async def check_project_limit(
    user_id: UUID, 
    db: AsyncSession, 
    project_id_to_exclude: UUID | None = None,
    new_project_is_public: bool = False
) -> None:
    """プロジェクト作成数の制限をチェックする.
    
    公開脚本を含むプロジェクトは制限カウントから除外される.
    非公開（プライベート）プロジェクトの上限は2つ.
    
    Args:
        user_id: ユーザーID
        db: DBセッション
        project_id_to_exclude: 更新時など、現在判定中のプロジェクトIDを除外する場合に指定
        new_project_is_public: 新規作成または更新後のプロジェクトが公開状態になるかどうか（Trueならカウントしない）
            ※ プロジェクトの公開状態 = 公開脚本を1つ以上含むかどうか
            
    Raises:
        HTTPException: 制限超過時
    """
    # ユーザーがオーナーの全プロジェクトを取得
    stmt = (
        select(TheaterProject)
        .join(ProjectMember)
        .where(
            ProjectMember.user_id == user_id,
            ProjectMember.role == "owner"
        )
        .options(selectinload(TheaterProject.scripts))
    )
    result = await db.execute(stmt)
    owned_projects = result.scalars().all()
    
    non_public_count = 0
    
    for project in owned_projects:
        # 除外対象ならスキップ（更新対象の現在の状態をカウントしないため）
        if project_id_to_exclude and project.id == project_id_to_exclude:
            continue
            
        # 公開脚本を含んでいるかチェック
        has_public_script = any(s.is_public for s in project.scripts)
        
        if not has_public_script:
            non_public_count += 1
            
    # 今回のアクションによる追加分
    # new_project_is_public=False (非公開) の場合、カウント+1
    if not new_project_is_public:
        non_public_count += 1
        
    if non_public_count > 2:
        raise HTTPException(
            status_code=400, 
            detail="非公開プロジェクトの作成上限（2つ）に達しています。新しいプロジェクトを作成するには、既存のプロジェクトを公開するか削除してください。"
        )
