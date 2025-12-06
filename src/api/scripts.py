"""脚本管理APIエンドポイント - 権限チェック付き."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProjectMember, Script, User, TheaterProject
from src.dependencies.auth import get_current_user_dep, get_optional_current_user_dep
from src.db import get_db
from src.schemas.script import ScriptListResponse, ScriptResponse
from src.services.fountain_parser import parse_fountain_and_create_models
from src.services.discord import DiscordService, get_discord_service

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
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
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
        uploaded_by=current_user.id,  # アップロードユーザーを記録
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
    
    # Discord通知
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"📝 **新しい脚本がアップロードされました**\nプロジェクト: {project.name}\nタイトル: {title}\nアップロード: {current_user.discord_username}",
        webhook_url=project.discord_webhook_url,
    )

    return ScriptResponse.model_validate(script)


@router.get("/{project_id}", response_model=ScriptListResponse)
async def list_scripts(
    project_id: int,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> ScriptListResponse:
    """プロジェクトの脚本一覧を取得.

    Args:
        project_id: プロジェクトID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        ScriptListResponse: 脚本一覧

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
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
    user: User | None = Depends(get_optional_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> ScriptResponse:
    """脚本詳細を取得.

    公開脚本は認証不要。非公開脚本はアップロードユーザーまたはプロジェクトメンバーのみ。

    Args:
        project_id: プロジェクトID
        script_id: 脚本ID
        user: 認証ユーザー（非必須）
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

    # 認証チェック（Depsで完了済み）

    # アクセス権チェック
    has_access = await _check_script_access(script, user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="この脚本へのアクセス権がありません")

    return ScriptResponse.model_validate(script)


@router.patch("/{script_id}/publicity")
async def update_script_publicity(
    script_id: int,
    is_public: bool = Form(...),
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """脚本の公開/非公開を切り替え.

    Args:
        script_id: 脚本ID
        is_public: 公開するか
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        dict: 成功メッセージ

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # アップロードユーザーまたはプロジェクトオーナーのみ変更可能
    is_uploader = script.uploaded_by == current_user.id

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == current_user.id,
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


@router.get("/{project_id}/{script_id}/pdf")
async def download_script_pdf(
    project_id: int,
    script_id: int,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """脚本をPDFとしてダウンロード.

    Args:
        project_id: プロジェクトID
        script_id: 脚本ID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        Response: PDFファイルバイナリ
    """
    from fastapi import Response
    from src.services.pdf_generator import generate_script_pdf

    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(
        select(Script).where(Script.id == script_id, Script.project_id == project_id)
    )
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # アクセス権チェック
    # PDFダウンロードは閲覧権限があれば可能とする
    has_access = await _check_script_access(script, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="この脚本へのアクセス権がありません")

    # PDF生成
    # script.content にFountainテキストが入っている前提
    if not script.content:
         raise HTTPException(status_code=400, detail="脚本コンテンツが空です")

    try:
        pdf_bytes = generate_script_pdf(script.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成に失敗しました: {e}")

    # 日本語ファイル名の文字化け対策（URLエンコードなど）は必要だが、
    # 簡易的にASCIIファイル名にするか、またはブラウザ周りの挙動に任せる
    # ここでは単純にタイトルを使用
    filename = f"{script.title}.pdf"
    
    # ascii以外の文字を含む場合のContent-Disposition対応は複雑なため、
    # シンプルに quote して渡すのが安全（RFC 5987）
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
