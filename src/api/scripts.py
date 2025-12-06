"""脚本管理APIエンドポイント."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import ProjectMember, Script
from src.schemas.script import ScriptListResponse, ScriptResponse
from src.services.fountain_parser import parse_fountain_and_create_models

router = APIRouter()


@router.post("/{project_id}/upload", response_model=ScriptResponse)
async def upload_script(
    project_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> ScriptResponse:
    """Fountain脚本をアップロード.

    Args:
        project_id: プロジェクトID
        title: 脚本タイトル
        file: Fountainファイル
        token: JWT トークン
        db: データベースセッション

    Returns:
        ScriptResponse: アップロードされた脚本

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # ファイル読み込み
    file_content = await file.read()
    fountain_text = file_content.decode("utf-8")

    # Scriptモデル作成（DB に直接保存）
    script = Script(
        project_id=project_id,
        title=title,
        content=fountain_text,  # Fountain内容を直接保存
    )
    db.add(script)
    await db.flush()

    # Fountainパースしてシーン・登場人物・セリフ作成
    await parse_fountain_and_create_models(script, fountain_text, db)

    await db.commit()
    await db.refresh(script)

    return ScriptResponse.model_validate(script)


@router.get("/{project_id}", response_model=list[ScriptListResponse])
async def list_scripts(
    project_id: int, token: str, db: AsyncSession = Depends(get_db)
) -> list[ScriptListResponse]:
    """プロジェクトの脚本一覧を取得.

    Args:
        project_id: プロジェクトID
        token: JWT トークン
        db: データベースセッション

    Returns:
        list[ScriptListResponse]: 脚本一覧

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # 脚本一覧取得
    result = await db.execute(select(Script).where(Script.project_id == project_id))
    scripts = result.scalars().all()

    return [ScriptListResponse.model_validate(s) for s in scripts]


@router.get("/{project_id}/{script_id}", response_model=ScriptResponse)
async def get_script(
    project_id: int, script_id: int, token: str, db: AsyncSession = Depends(get_db)
) -> ScriptResponse:
    """脚本詳細を取得.

    Args:
        project_id: プロジェクトID
        script_id: 脚本ID
        token: JWT トークン
        db: データベースセッション

    Returns:
        ScriptResponse: 脚本詳細

    Raises:
        HTTPException: 認証エラー、権限エラー、または脚本が見つからない
    """
    # 認証チェック
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # 脚本取得
    result = await db.execute(
        select(Script).where(Script.id == script_id, Script.project_id == project_id)
    )
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    return ScriptResponse.model_validate(script)
