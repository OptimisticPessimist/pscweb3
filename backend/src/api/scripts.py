"""脚本管理APIエンドポイント - 権限チェック付き."""

from urllib.parse import quote
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import (
    Character,
    Line,
    ProjectMember,
    Scene,
    Script,
    TheaterProject,
    User,
)
from src.dependencies.auth import get_current_user_dep
from src.dependencies.permissions import get_project_member_dep, get_script_member_dep
from src.schemas.script import ScriptListResponse, ScriptResponse
from src.services.discord import DiscordService, get_discord_service
from src.services.pdf_generator import generate_script_pdf

router = APIRouter(tags=["scripts"])


# ===========================
# Scripts List & Detail
# ===========================


@router.get("/{project_id}", response_model=ScriptListResponse)
async def get_scripts(
    project_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> ScriptListResponse:
    """プロジェクトの脚本一覧を取得."""
    # 権限チェックはDepends(get_project_member_dep)で完了済み

    # 脚本取得
    stmt = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(
            selectinload(Script.characters).selectinload(Character.castings),
            selectinload(Script.scenes).options(
                selectinload(Scene.lines).options(
                    selectinload(Line.character).selectinload(Character.castings)
                )
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
    author: str | None = Form(None),
    script_file: UploadFile = File(...),
    is_public: str = Form("false"),  # 型変換エラー回避のため str で受け取る
    public_terms: str | None = Form(None),
    public_contact: str | None = Form(None),
    pdf_orientation: str = Form("landscape"),
    pdf_writing_direction: str = Form("vertical"),
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> ScriptResponse:
    """Fountain脚本をアップロード."""
    from src.services.script_notification import send_script_notification
    from src.services.script_processor import (
        process_script_upload,
        validate_upload_request,
    )

    # デバッグログ
    print(f"[Upload Debug] project_id={project_id}, title={title}, author={author}, is_public={is_public}")
    print(f"[Upload Debug] script_file={script_file.filename if script_file else 'None'}")

    # is_public の変換
    is_public_bool = str(is_public).lower() == "true"

    # 1. リクエスト検証
    await validate_upload_request(project_id, current_user, script_file.filename, db)

    # 2. ファイル読み込みとエンコーディング判別
    file_content = await script_file.read()
    
    fountain_text = None
    for encoding in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            fountain_text = file_content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if fountain_text is None:
        try:
            import charset_normalizer
            result = charset_normalizer.from_bytes(file_content).best()
            if result and result.encoding:
                fountain_text = str(result)
        except Exception:
            pass

    if fountain_text is None:
        raise HTTPException(status_code=400, detail="ファイルのエンコーディングを判別できませんでした (UTF-8 または Shift_JIS にてアップロードしてください)")

    # 3. スクリプト処理
    try:
        script, is_update = await process_script_upload(
            project_id,
            current_user.id,
            title,
            author,
            fountain_text,
            is_public_bool,
            db,
            public_terms=public_terms,
            public_contact=public_contact,
            pdf_orientation=pdf_orientation,
            pdf_writing_direction=pdf_writing_direction,
        )
    except Exception as e:
        import traceback

        print(f"[Upload Failed] {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload Failed: {str(e)}")

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
    tuple_data: tuple[ProjectMember, Script] = Depends(get_script_member_dep),
) -> ScriptResponse:
    """指定した脚本の詳細を取得."""
    # 権限チェックはDepends(get_project_member_dep)で完了済み

    member, script = tuple_data
    return ScriptResponse.model_validate(script)


@router.get("/{project_id}/{script_id}/pdf")
async def download_script_pdf(
    tuple_data: tuple[ProjectMember, Script] = Depends(get_script_member_dep),
    orientation: str | None = Query(None, description="Paper orientation: landscape or portrait"),
    writing_direction: str | None = Query(
        None, description="Writing direction: vertical or horizontal"
    ),
):
    """脚本のPDFをダウンロード."""
    # 権限チェックはDepends(get_script_member_dep)内で完了済み
    member, script = tuple_data

    # パラメータバリデーション（指定がない場合はScriptの保存設定を使用）
    if not orientation:
        orientation = script.pdf_orientation or "landscape"
    if orientation not in ("landscape", "portrait"):
        orientation = "landscape"

    if not writing_direction:
        writing_direction = script.pdf_writing_direction or "vertical"
    if writing_direction not in ("vertical", "horizontal"):
        writing_direction = "vertical"

    # PDF生成
    try:
        pdf_bytes = generate_script_pdf(
            script.content,
            orientation=orientation,
            writing_direction=writing_direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    # ファイル名生成（ASCII文字以外を含む可能性を考慮し、Headerで指定推奨だが今回はシンプルに）
    # 必要であれば urllib.parse.quote でエンコードするなど検討
    filename = f"{script.title}.pdf"
    filename_encoded = quote(filename)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"},
    )


# ===========================
# Scenes
# ===========================


@router.get("/{project_id}/{script_id}/scenes")
async def get_scenes(
    project_id: UUID,
    script_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
):
    """指定した脚本のシーン一覧を取得."""
    # 権限チェックはDepends(get_project_member_dep)で完了済み

    # シーン取得
    result = await db.execute(
        select(Scene)
        .where(Scene.script_id == script_id)
        .where(Scene.scene_number > 0)
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
    member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
):
    """指定した脚本の登場人物一覧を取得."""
    # 権限チェックはDepends(get_project_member_dep)で完了済み

    # 登場人物取得
    result = await db.execute(select(Character).where(Character.script_id == script_id))
    characters = result.scalars().all()

    return {"characters": characters}
