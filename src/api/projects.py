"""プロジェクト管理APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import ProjectMember, TheaterProject, User

router = APIRouter()


class ProjectCreate(BaseModel):
    """プロジェクト作成リクエスト."""

    name: str = Field(..., description="プロジェクト名")
    description: str | None = Field(None, description="説明")


class ProjectResponse(BaseModel):
    """プロジェクトレスポンス."""

    id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="プロジェクト名")
    description: str | None = Field(None, description="説明")

    model_config = {"from_attributes": True}


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """プロジェクトを作成.
    
    Args:
        project_data: プロジェクト作成データ
        token: JWT トークン
        db: データベースセッション
        
    Returns:
        ProjectResponse: 作成されたプロジェクト
        
    Raises:
        HTTPException: 認証エラー
    """
    user = await get_current_user(token, db)
    if user is None:
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
        user_id=user.id,
        role="owner",
    )
    db.add(member)

    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """参加中のプロジェクト一覧を取得.
    
    Args:
        token: JWT トークン
        db: データベースセッション
        
    Returns:
        list[ProjectResponse]: プロジェクトリスト
        
    Raises:
        HTTPException: 認証エラー
    """
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # ユーザーが参加しているプロジェクト一覧を取得
    result = await db.execute(
        select(TheaterProject)
        .join(ProjectMember)
        .where(ProjectMember.user_id == user.id)
    )
    projects = result.scalars().all()

    return [ProjectResponse.model_validate(p) for p in projects]
