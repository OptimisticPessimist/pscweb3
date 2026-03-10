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
    TheaterProject,
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
    
    if member.role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=403, detail="権限がありません（閲覧者はアップロードできません）"
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
    author: str | None,
    fountain_text: str,
    is_public: bool,
    db: AsyncSession,
    public_terms: str | None = None,
    public_contact: str | None = None,
    pdf_orientation: str = "landscape",
    pdf_writing_direction: str = "vertical",
) -> tuple[Script, bool]:
    """既存スクリプトを取得、または新規作成.
    
    Args:
        project_id: プロジェクトID
        user_id: ユーザーID
        title: スクリプトタイトル
        author: 著者
        fountain_text: Fountainテキスト
        is_public: 公開フラグ
        db: データベースセッション
        public_terms: 使用条件
        public_contact: 連絡先
    
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
        script.author = author
        script.content = fountain_text
        script.uploaded_by = user_id
        script.uploaded_at = datetime.now(timezone.utc)
        script.is_public = is_public
        script.public_terms = public_terms
        script.public_contact = public_contact
        script.pdf_orientation = pdf_orientation
        script.pdf_writing_direction = pdf_writing_direction
        script.revision += 1
    else:
        # 新規作成
        script = Script(
            project_id=project_id,
            uploaded_by=user_id,
            title=title,
            author=author,
            content=fountain_text,
            is_public=is_public,
            public_terms=public_terms,
            public_contact=public_contact,
            pdf_orientation=pdf_orientation,
            pdf_writing_direction=pdf_writing_direction,
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


async def collect_associations(script_id: UUID, db: AsyncSession):
    """削除前に重要な紐付け情報を収集."""
    # 1. 配役情報 (名前ベース)
    casting_stmt = (
        select(Character.name, CharacterCasting.user_id, CharacterCasting.cast_name)
        .join(CharacterCasting, Character.id == CharacterCasting.character_id)
        .where(Character.script_id == script_id)
    )
    castings = (await db.execute(casting_stmt)).all()

    # 2. 稽古-シーン紐付け (見出しと番号ベース)
    re_scene_stmt = (
        select(RehearsalScene.rehearsal_id, Scene.heading, Scene.act_number, Scene.scene_number)
        .join(Scene, RehearsalScene.scene_id == Scene.id)
        .where(Scene.script_id == script_id)
    )
    re_scenes = (await db.execute(re_scene_stmt)).all()

    # 3. 稽古単体シーン紐付け (Rehearsal.scene_id)
    re_single_stmt = (
        select(Rehearsal.id, Scene.heading, Scene.act_number, Scene.scene_number)
        .join(Scene, Rehearsal.scene_id == Scene.id)
        .where(Scene.script_id == script_id)
    )
    re_singles = (await db.execute(re_single_stmt)).all()

    # 4. 稽古ごとのキャスト指定 (RehearsalCast)
    re_cast_stmt = (
        select(RehearsalCast.rehearsal_id, Character.name, RehearsalCast.user_id)
        .join(Character, RehearsalCast.character_id == Character.id)
        .where(Character.script_id == script_id)
    )
    re_casts = (await db.execute(re_cast_stmt)).all()

    return {
        "castings": castings,
        "re_scenes": re_scenes,
        "re_singles": re_singles,
        "re_casts": re_casts,
    }


async def restore_associations(script: Script, data: dict, db: AsyncSession):
    """情報を新しいIDに紐付け直す."""
    # 新しいキャラクターとシーンをロード
    await db.refresh(script, ["characters", "scenes"])
    
    char_map = {c.name: c.id for c in script.characters}
    
    # 1. 配役の復元
    for char_name, user_id, cast_name in data["castings"]:
        if char_name in char_map:
            db.add(CharacterCasting(
                character_id=char_map[char_name],
                user_id=user_id,
                cast_name=cast_name
            ))
            
    # 2. 稽古-シーン(多対多)の復元
    for rehearsal_id, heading, act, scene_num in data["re_scenes"]:
        # 見出しとAct/Scene番号でマッチするものを探す
        matched_scene = None
        for s in script.scenes:
            if s.heading == heading and s.act_number == act and s.scene_number == scene_num:
                matched_scene = s
                break
        
        if not matched_scene:
            # 見出しだけ同じものを探す（フォールバック）
            for s in script.scenes:
                if s.heading == heading:
                    matched_scene = s
                    break
        
        if matched_scene:
            db.add(RehearsalScene(rehearsal_id=rehearsal_id, scene_id=matched_scene.id))

    # 3. 稽古単体シーン(Rehearsal.scene_id)の復元
    for rehearsal_id, heading, act, scene_num in data["re_singles"]:
        matched_scene = None
        for s in script.scenes:
            if s.heading == heading and s.act_number == act and s.scene_number == scene_num:
                matched_scene = s
                break
        
        if matched_scene:
            await db.execute(
                update(Rehearsal)
                .where(Rehearsal.id == rehearsal_id)
                .values(scene_id=matched_scene.id)
            )

    # 4. 稽古ごとのキャスト指定 (RehearsalCast)
    for rehearsal_id, char_name, user_id in data["re_casts"]:
        if char_name in char_map:
            db.add(RehearsalCast(
                rehearsal_id=rehearsal_id,
                character_id=char_map[char_name],
                user_id=user_id
            ))

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
    author: str | None,
    fountain_text: str,
    is_public: bool,
    db: AsyncSession,
    public_terms: str | None = None,
    public_contact: str | None = None,
    pdf_orientation: str = "landscape",
    pdf_writing_direction: str = "vertical",
) -> tuple[Script, bool]:
    """スクリプトアップロード処理のメインロジック.
    
    Args:
        project_id: プロジェクトID
        user_id: ユーザーID
        title: スクリプトタイトル
        author: 著者
        fountain_text: Fountainテキスト
        is_public: 公開フラグ
        db: データベースセッション
        public_terms: 使用条件
        public_contact: 連絡先
    
    Returns:
        tuple[Script, bool]: (処理済みスクリプト, 更新フラグ)
    """
    from src.services.project_limit import check_project_limit
    
    # プロジェクト数制限チェック (Loophole Prevention)
    # 脚本の公開/非公開設定によって、プロジェクトが「非公開」としてカウントされるかどうかが変わる
    # 既存プロジェクトのため、自分自身を除外して再計算する
    # ※ 現在は1プロジェクト1脚本制であるため、この脚本設定がプロジェクト全体の属性になる
    await check_project_limit(
        user_id=user_id,
        db=db,
        project_id_to_exclude=project_id,
        new_project_is_public=is_public
    )

    # スクリプトの取得または作成
    script, is_update = await get_or_create_script(
        project_id, user_id, title, author, fountain_text, is_public, db,
        public_terms=public_terms, public_contact=public_contact,
        pdf_orientation=pdf_orientation, pdf_writing_direction=pdf_writing_direction
    )
    
    # 更新の場合は関連データを削除
    if is_update:
        # Before cleanup, collect data to restore
        associations = await collect_associations(script.id, db)
        await cleanup_related_data(script, db)
        await db.refresh(script)
        
    # プロジェクトの公開設定を同期 (1プロジェクト1脚本のため、脚本の設定=プロジェクトの設定)
    project = await db.get(TheaterProject, project_id)
    if project:
        project.is_public = is_public
        db.add(project)
    
    # Fountainパースと保存
    script = await parse_and_save_fountain(script, fountain_text, db)
    
    # Restore associations
    if is_update:
        await restore_associations(script, associations, db)
        await db.commit() # Save restored data
    
    return script, is_update
