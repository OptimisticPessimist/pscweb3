"""脚本管理APIエンドポイント - 権限チェック付き."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import ProjectMember, Script, User
from src.schemas.script import ScriptListResponse, ScriptResponse
from src.services.fountain_parser import parse_fountain_and_create_models

router = APIRouter()


async def _check_script_access(
    script: Script, user: User | None, db: AsyncSession
) -> bool:
    """脚本へのアクセス権をチェック.

    Args:
        script: 脚本モデル
        user: ユーザー（未認証の場合None）
        db: データベースセッション

    Returns:
        bool: アクセス権があればTrue
    """
    # 公開脚本は誰でもアクセス可能
    if script.is_public:
        return True

    # 未認証ユーザーは非公開脚本にアクセス不可
    if user is None:
        return False

    # アップロードユーザーは常にアクセス可能
    if script.uploaded_by == user.id:
        return True

    # プロジェクトメンバーはアクセス可能
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    return member is not None


@router.post("/{project_id}/upload", response_model=ScriptResponse)
async def upload_script(
    project_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> ScriptResponse:
    """Fountain脚本をアップロード.

    Args:
        project_id: プロジェクトID
        title: 脚本タイトル
        file: Fountainファイル
        is_public: 全体公開するか（デフォルト: False）
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
        uploaded_by=user.id,  # アップロードユーザーを記録
        title=title,
        content=fountain_text,  # Fountain内容を直接保存
        is_public=is_public,
    )
    db.add(script)
    await db.flush()

    # Fountainパースしてシーン・登場人物・セリフ作成
    await parse_fountain_and_create_models(script, fountain_text, db)

    await db.commit()
    await db.refresh(script)

    return ScriptResponse.model_validate(script)


@router.get("/{project_id}", response_model=ScriptListResponse)
async def list_scripts(
    project_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> ScriptListResponse:
    """プロジェクトの脚本一覧を取得.

    Args:
        project_id: プロジェクトID
        token: JWT トークン
        db: データベースセッション

    Returns:
        ScriptListResponse: 脚本一覧

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

    return ScriptListResponse(scripts=[ScriptResponse.model_validate(s) for s in scripts])


@router.get("/{project_id}/{script_id}", response_model=ScriptResponse)
async def get_script(
    project_id: int,
    script_id: int,
    token: str = Query(None),  # 公開脚本の場合は認証不要
    db: AsyncSession = Depends(get_db),
) -> ScriptResponse:
    """脚本詳細を取得.

    公開脚本は認証不要。非公開脚本はアップロードユーザーまたはプロジェクトメンバーのみ。

    Args:
        project_id: プロジェクトID
        script_id: 脚本ID
        token: JWT トークン（公開脚本の場合は省略可）
        db: データベースセッション

    Returns:
        ScriptResponse: 脚本詳細

    Raises:
        HTTPException: 脚本が見つからない、または権限エラー
    """
    # 脚本取得
    result = await db.execute(
        select(Script).where(Script.id == script_id, Script.project_id == project_id)
    )
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # 認証チェック（tokenがある場合のみ）
    user = None
    if token:
        user = await get_current_user(token, db)

    # アクセス権チェック
    has_access = await _check_script_access(script, user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="この脚本へのアクセス権がありません")

    return ScriptResponse.model_validate(script)


@router.patch("/{script_id}/publicity")
async def update_script_publicity(
    script_id: int,
    is_public: bool = Form(...),
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """脚本の公開/非公開を切り替え.

    Args:
        script_id: 脚本ID
        is_public: 公開するか
        token: JWT トークン
        db: データベースセッション

    Returns:
        dict: 成功メッセージ

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # アップロードユーザーまたはプロジェクトオーナーのみ変更可能
    is_uploader = script.uploaded_by == user.id

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    is_owner = member is not None and member.role == "owner"

    if not (is_uploader or is_owner):
        raise HTTPException(status_code=403, detail="この脚本の公開設定を変更する権限がありません")

    # 公開設定更新
    script.is_public = is_public
    await db.commit()

    status = "公開" if is_public else "非公開"
    return {"message": f"脚本を{status}に設定しました"}
