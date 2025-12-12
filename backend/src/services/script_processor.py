"""スクリプト処理サービス."""

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from src.db.models import (
    Script,
    Scene,
    Character,
    Line,
    SceneChart,
    SceneCharacterMapping,
    CharacterCasting,
    Rehearsal,
    RehearsalScene,
    RehearsalCast,
    User,
    ProjectMember,
)


async def validate_upload_request(
    project_id: UUID,
    current_user: User,
    filename: str,
    db: AsyncSession,
) -> ProjectMember:
    """脚本アップロードリクエストの検証.
    
    Args:
        project_id: プロジェクトID
        current_user: 認証ユーザー
        filename: アップロードファイル名
        db: データベースセッション
    
    Returns:
        ProjectMember: プロジェクトメンバー情報
    
    Raises:
        HTTPException: 認証エラー、権限エラー、ファイル形式エラー
    """
    # 認証チェック
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")
    
    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=403, detail="このプロジェクトへのアクセス権がありません"
        )
    
    # ファイル拡張子チェック
    if not filename.endswith(".fountain"):
        raise HTTPException(
            status_code=400, detail="Fountainファイル(.fountain)のみアップロード可能です"
        )
    
    return member


async def get_or_create_script(
    project_id: UUID,
    user_id: UUID,
    title: str,
    fountain_text: str,
    is_public: bool,
    db: AsyncSession,
) -> tuple[Script, bool]:
    """既存スクリプトを取得、または新規作成.
    
    Args:
        project_id: プロジェクトID
        user_id: ユーザーID
        title: スクリプトタイトル
        fountain_text: Fountainテキスト
        is_public: 公開フラグ
        db: データベースセッション
    
    Returns:
        tuple[Script, bool]: (スクリプト, 更新フラグ)
    """
    # プロジェクトに既存の脚本があるか確認
    result = await db.execute(select(Script).where(Script.project_id == project_id))
    existing_scripts = result.scalars().all()
    
    is_update = False
    
    if existing_scripts:
        # 既存スクリプトがある場合（1プロジェクト1脚本制）
        script = existing_scripts[0]
        is_update = True
        
        # 重複削除
        if len(existing_scripts) > 1:
            for duplicate in existing_scripts[1:]:
                await db.delete(duplicate)
        
        # Update existing script
        script.title = title
        script.content = fountain_text
        script.uploaded_by = user_id
        script.uploaded_at = datetime.now(timezone.utc)
        script.is_public = is_public
        script.revision += 1
    else:
        # 新規作成
        script = Script(
            project_id=project_id,
            uploaded_by=user_id,
            title=title,
            content=fountain_text,
            is_public=is_public,
        )
        db.add(script)
        await db.flush()
    
    return script, is_update


async def cleanup_related_data(script: Script, db: AsyncSession) -> None:
    """スクリプトに関連する古いデータを削除.
    
    Args:
        script: スクリプト
        db: データベースセッション
    """
    # 1. 香盤表とマッピング
    chart_result = await db.execute(
        select(SceneChart.id).where(SceneChart.script_id == script.id)
    )
    chart_ids = [r for r in chart_result.scalars().all()]
    
    if chart_ids:
        await db.execute(
            delete(SceneCharacterMapping).where(
                SceneCharacterMapping.chart_id.in_(chart_ids)
            )
        )
        await db.execute(delete(SceneChart).where(SceneChart.id.in_(chart_ids)))
    
    # 2. セリフ (SceneとCharacterに依存)
    scene_result = await db.execute(
        select(Scene.id).where(Scene.script_id == script.id)
    )
    scene_ids = [r for r in scene_result.scalars().all()]
    
    if scene_ids:
        # RehearsalSceneを先に削除 (rehearsal_scenes テーブル)
        await db.execute(
            delete(RehearsalScene).where(RehearsalScene.scene_id.in_(scene_ids))
        )
        
        # Rehearsalのscene_idをNULLにする (稽古自体は残す)
        await db.execute(
            update(Rehearsal)
            .where(Rehearsal.scene_id.in_(scene_ids))
            .values(scene_id=None)
        )
        
        await db.execute(delete(Line).where(Line.scene_id.in_(scene_ids)))
    
    # 3. シーン
    await db.execute(delete(Scene).where(Scene.script_id == script.id))
    
    # 4. キャラクター (CharacterCasting, RehearsalCastも削除)
    character_result = await db.execute(
        select(Character.id).where(Character.script_id == script.id)
    )
    character_ids = [r for r in character_result.scalars().all()]
    
    if character_ids:
        await db.execute(
            delete(CharacterCasting).where(
                CharacterCasting.character_id.in_(character_ids)
            )
        )
        await db.execute(
            delete(RehearsalCast).where(RehearsalCast.character_id.in_(character_ids))
        )
    
    await db.execute(delete(Character).where(Character.script_id == script.id))
    
    await db.flush()


async def parse_and_save_fountain(
    script: Script, fountain_text: str, db: AsyncSession
) -> Script:
    """Fountainテキストをパースしてデータベースに保存.
    
    Args:
        script: スクリプト
        fountain_text: Fountainテキスト
        db: データベースセッション
    
    Returns:
        Script: リレーションがロードされたスクリプト
    
    Raises:
        HTTPException: パース失敗時
    """
    from src.services.fountain_parser import parse_fountain_and_create_models
    from src.services.scene_chart_generator import generate_scene_chart
    
    try:
        # Fountainパース
        await parse_fountain_and_create_models(script, fountain_text, db)
        
        # リレーションをロード
        stmt = (
            select(Script)
            .where(Script.id == script.id)
            .options(
                selectinload(Script.scenes).options(
                    selectinload(Scene.lines).options(
                        selectinload(Line.character).selectinload(Character.castings)
                    )
                ),
                selectinload(Script.characters).selectinload(Character.castings),
            )
        )
        result = await db.execute(stmt)
        script = result.scalar_one()
        
        # 香盤表の自動生成
        await generate_scene_chart(script, db)
        
        await db.commit()
        
        # 再取得（確実にロードされた状態にする）
        result = await db.execute(stmt)
        script = result.scalar_one()
        
        return script
        
    except Exception as e:
        await db.rollback()
        import traceback
        error_msg = traceback.format_exc()
        
        # デバッグログ出力（console only - Azure is read-only filesystem）
        print(f"[Script Upload Error] {error_msg}")
        
        raise HTTPException(
            status_code=500,
            detail=f"脚本の解析またはデータ保存中にエラーが発生しました: {str(e)}",
        )


async def process_script_upload(
    project_id: UUID,
    user_id: UUID,
    title: str,
    fountain_text: str,
    is_public: bool,
    db: AsyncSession,
) -> tuple[Script, bool]:
    """スクリプトアップロード処理のメインロジック.
    
    Args:
        project_id: プロジェクトID
        user_id: ユーザーID
        title: スクリプトタイトル
        fountain_text: Fountainテキスト
        is_public: 公開フラグ
        db: データベースセッション
    
    Returns:
        tuple[Script, bool]: (処理済みスクリプト, 更新フラグ)
    """
    # スクリプトの取得または作成
    script, is_update = await get_or_create_script(
        project_id, user_id, title, fountain_text, is_public, db
    )
    
    # 更新の場合は関連データを削除
    if is_update:
        await cleanup_related_data(script, db)
        await db.refresh(script)
    
    # Fountainパースと保存
    script = await parse_and_save_fountain(script, fountain_text, db)
    
    return script, is_update
