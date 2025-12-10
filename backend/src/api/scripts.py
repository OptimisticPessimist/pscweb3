"""脚本管理APIエンドポイント - 権限チェック付き."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import (
    ProjectMember, Script, User, TheaterProject, Scene, Line, Character,
    SceneChart, SceneCharacterMapping, Rehearsal, CharacterCasting, RehearsalCast
)
from src.dependencies.auth import get_current_user_dep, get_optional_current_user_dep
from src.db import get_db
from src.schemas.script import ScriptListResponse, ScriptResponse, ScriptSummary
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

    # ファイル拡張子チェック
    if not file.filename.endswith(".fountain"):
        raise HTTPException(status_code=400, detail="Fountainファイル(.fountain)のみアップロード可能です")

    # ファイル読み込み
    file_content = await file.read()
    fountain_text = file_content.decode("utf-8")

    # プロジェクトに既存の脚本があるか確認
    result = await db.execute(select(Script).where(Script.project_id == project_id))
    existing_scripts = result.scalars().all()
    
    existing_script = None
    is_update = False
    
    if existing_scripts:
        # 既存スクリプトがある場合
        # 1プロジェクト1脚本制のため、重複がある場合は先頭以外を削除して整合性を保つ
        existing_script = existing_scripts[0]
        script = existing_script
        is_update = True
        
        # 重複削除
        if len(existing_scripts) > 1:
            for duplicate in existing_scripts[1:]:
                await db.delete(duplicate)
        
        # Update existing script
        existing_script.title = title
        existing_script.content = fountain_text
        existing_script.uploaded_by = current_user.id
        existing_script.uploaded_at = datetime.utcnow() # 更新日時を現在に
        existing_script.is_public = is_public
        existing_script.revision += 1  # リビジョンを加算
        
        # Clear old related data (Scenes, Characters, SceneCharts)
        from sqlalchemy import delete
        
        # 依存関係の順序で削除
        
        # 依存関係の順序で削除
        
        # 1. 香盤表とマッピング
        # SceneChartを特定
        chart_result = await db.execute(select(SceneChart.id).where(SceneChart.script_id == script.id))
        chart_ids = [r for r in chart_result.scalars().all()]
        
        if chart_ids:
            await db.execute(delete(SceneCharacterMapping).where(SceneCharacterMapping.chart_id.in_(chart_ids)))
            await db.execute(delete(SceneChart).where(SceneChart.id.in_(chart_ids)))
            
        # 2. セリフ (SceneとCharacterに依存)
        # 関連するSceneのIDを取得
        scene_result = await db.execute(select(Scene.id).where(Scene.script_id == script.id))
        scene_ids = [r for r in scene_result.scalars().all()]
        
        if scene_ids:
            # Rehearsalのscene_idをNULLにする (稽古自体は残す)
            from sqlalchemy import update
            await db.execute(
                update(Rehearsal)
                .where(Rehearsal.scene_id.in_(scene_ids))
                .values(scene_id=None)
            )
            
            await db.execute(delete(Line).where(Line.scene_id.in_(scene_ids)))
        
        # 3. シーン (Characterには依存しないが、Lineの親)
        await db.execute(delete(Scene).where(Scene.script_id == script.id))
        
        # 4. キャラクター (Lineなどに依存される)
        # CharacterCasting, RehearsalCastも削除が必要
        character_result = await db.execute(select(Character.id).where(Character.script_id == script.id))
        character_ids = [r for r in character_result.scalars().all()]
        if character_ids:
             await db.execute(delete(CharacterCasting).where(CharacterCasting.character_id.in_(character_ids)))
             await db.execute(delete(RehearsalCast).where(RehearsalCast.character_id.in_(character_ids)))

        await db.execute(delete(Character).where(Character.script_id == script.id))
        
        await db.flush()
        
        # 削除後、scriptインスタンスのリレーションをリフレッシュして古いオブジェクトの参照を切る
        await db.refresh(script)
        
    else:
        # Scriptモデル新規作成
        script = Script(
            project_id=project_id,
            uploaded_by=current_user.id,
            title=title,
            content=fountain_text,
            is_public=is_public,
        )
        db.add(script)
        await db.flush()

    # Fountainパースしてシーン・登場人物・セリフ作成
    try:
        await parse_fountain_and_create_models(script, fountain_text, db)
        
        # 新しく作成されたシーンを認識させるためにリフレッシュ
        # N+1対策: 明示的にリレーションをロード
        stmt = (
            select(Script)
            .where(Script.id == script.id)
            .options(
                selectinload(Script.scenes).options(
                    selectinload(Scene.lines).options(
                        selectinload(Line.character)
                    )
                ),
                selectinload(Script.characters)
            )
        )
        result = await db.execute(stmt)
        script = result.scalar_one()

        # 香盤表の自動生成
        from src.services.scene_chart_generator import generate_scene_chart
        await generate_scene_chart(script, db)

        await db.commit()

        # レスポンス生成のために再取得（確実にロードされた状態にする）
        result = await db.execute(stmt)
        script = result.scalar_one()


    except Exception as e:
        await db.rollback()
        import traceback
        error_msg = traceback.format_exc()
        # ファイルにエラーログを出力
        with open("debug_panic.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Script Upload Error: {str(e)}\n{error_msg}\n")
        print(error_msg) # consoleにも出す
        raise HTTPException(status_code=500, detail=f"脚本の解析またはデータ保存中にエラーが発生しました: {str(e)}")
    # await db.refresh(script) # 上記でロード済みのため不要

    
    # Discord通知
    project = await db.get(TheaterProject, project_id)
    
    action_text = "更新" if is_update else "新規アップロード"
    revision_text = f" (Rev.{script.revision})" if script.revision > 1 else ""
    message = f"📝 **脚本が{action_text}されました{revision_text}**\nプロジェクト: {project.name}\nタイトル: {title}\nユーザー: {current_user.discord_username}"
    
    # PDF生成（通知添付用）
    pdf_file = None
    try:
        from src.services.pdf_generator import generate_script_pdf
        pdf_bytes = generate_script_pdf(script.content)
        pdf_file = {
            "filename": f"{title}.pdf",
            "content": pdf_bytes
        }
    except Exception as e:
        # PDF生成失敗しても通知は送る
        message += f"\n\n⚠️ PDF生成に失敗しました: {e}"

    background_tasks.add_task(
        discord_service.send_notification,
        content=message,
        webhook_url=project.discord_webhook_url,
        file=pdf_file
    )

    return ScriptResponse.model_validate(script)


@router.get("/{project_id}", response_model=ScriptListResponse)
async def list_scripts(
    project_id: UUID,
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

    return ScriptListResponse(scripts=[ScriptSummary.model_validate(s) for s in scripts])


@router.get("/{project_id}/{script_id}", response_model=ScriptResponse)
async def get_script(
    project_id: UUID,
    script_id: UUID,
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
    # 脚本取得（関連データもロード）
    result = await db.execute(
        select(Script)
        .where(Script.id == script_id, Script.project_id == project_id)
        .options(
            selectinload(Script.scenes).selectinload(Scene.lines).selectinload(Line.character),
            selectinload(Script.characters)
        )
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
    script_id: UUID,
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
    project_id: UUID,
    script_id: UUID,
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


@router.delete("/{project_id}/{script_id}")
async def delete_script(
    project_id: UUID,
    script_id: UUID,
    current_user: User | None = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """脚本を削除.

    Args:
        project_id: プロジェクトID
        script_id: 脚本ID
        current_user: 認証ユーザー
        db: データベースセッション

    Returns:
        dict: 成功メッセージ

    Raises:
        HTTPException: 権限エラーまたは見つからない場合
    """
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

    # 権限チェック: アップロードユーザー または プロジェクトオーナーのみ削除可能
    is_uploader = script.uploaded_by == current_user.id

    if is_uploader:
        has_permission = True
    else:
        # プロジェクトメンバーシップとロールを確認
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id,
            )
        )
        member = result.scalar_one_or_none()
        has_permission = member is not None and member.role == "owner"

    if not has_permission:
        raise HTTPException(status_code=403, detail="この脚本を削除する権限がありません")

    # 削除実行 (cascade設定により関連データも削除されるはず)
    await db.delete(script)
    await db.commit()

    return {"message": "脚本を削除しました"}
