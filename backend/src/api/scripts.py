"""脚本管理APIエンドポイント - 権限チェック付き."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import (
    Character,
    CharacterCasting,
    Line,
    ProjectMember,
    Rehearsal,
    RehearsalCast,
    Scene,
    SceneChart,
    SceneCharacterMapping,
    Script,
    TheaterProject,
    User,
)
from src.dependencies.auth import get_current_user_dep
from src.schemas.script import ScriptListResponse, ScriptResponse
from src.services.fountain_parser import parse_fountain_and_create_models
from src.services.scene_chart_generator import generate_scene_chart
from src.services.discord import DiscordService, get_discord_service

router = APIRouter(tags=["scripts"])


# ===========================
# Scripts List & Detail
# ===========================

@router.get("/{project_id}", response_model=ScriptListResponse)
async def get_scripts(
    project_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> ScriptListResponse:
    """プロジェクトの脚本一覧を取得."""
    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # 脚本取得
    stmt = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(
            selectinload(Script.characters),
            selectinload(Script.scenes).options(
                selectinload(Scene.lines).options(selectinload(Line.character))
            ),
        )
    )
    result = await db.execute(stmt)
    scripts = result.scalars().all()
    return ScriptListResponse(scripts=[ScriptResponse.model_validate(s) for s in scripts])


@router.post("/{project_id}/upload", response_model=ScriptResponse)
async def upload_script(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> ScriptResponse:
    """Fountain脚本をアップロード.

    Args:
        project_id: プロジェクトID
        background_tasks: バックグラウンドタスク
        title: 脚本タイトル
        file: Fountainファイル
        is_public: 全体公開するか（デフォルト: False）
        current_user: 認証ユーザー
        db: データベースセッション
        discord_service: Discordサービス

    Returns:
        ScriptResponse: アップロードされた脚本

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    from src.services.script_processor import (
        validate_upload_request,
        process_script_upload,
    )
    from src.services.script_notification import send_script_notification

    # 1. リクエスト検証
    await validate_upload_request(project_id, current_user, file.filename, db)

    # 2. ファイル読み込み
    file_content = await file.read()
    fountain_text = file_content.decode("utf-8")

    # 3. スクリプト処理
    script, is_update = await process_script_upload(
        project_id, current_user.id, title, fountain_text, is_public, db
    )

    # 4. Discord通知（バックグラウンド）
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        send_script_notification,
        script,
        project,
        current_user,
        is_update,
        discord_service,
    )

    return ScriptResponse.model_validate(script)


@router.get("/{project_id}/{script_id}", response_model=ScriptResponse)
async def get_script(
    project_id: UUID,
    script_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> ScriptResponse:
    """指定した脚本の詳細を取得."""
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

    # 脚本取得
    result = await db.execute(
        select(Script).where(Script.id == script_id, Script.project_id == project_id)
    )
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    return ScriptResponse.model_validate(script)


# ===========================
# Scenes
# ===========================

@router.get("/{project_id}/{script_id}/scenes")
async def get_scenes(
    project_id: UUID,
    script_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """指定した脚本のシーン一覧を取得."""
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

    # シーン取得
    result = await db.execute(
        select(Scene)
        .where(Scene.script_id == script_id)
        .order_by(Scene.act_number, Scene.scene_number)
    )
    scenes = result.scalars().all()

    return {"scenes": scenes}


# ===========================
# Characters
# ===========================

@router.get("/{project_id}/{script_id}/characters")
async def get_characters(
    project_id: UUID,
    script_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """指定した脚本の登場人物一覧を取得."""
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

    # 登場人物取得
    result = await db.execute(select(Character).where(Character.script_id == script_id))
    characters = result.scalars().all()

    return {"characters": characters}
