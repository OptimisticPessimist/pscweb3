"""キャラクターおよびキャスティング管理APIエンドポイント."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import (
    AuditLog,
    Character,
    CharacterCasting,
    ProjectMember,
    Script,
    TheaterProject,
    User,
)
from src.dependencies.permissions import get_project_editor_dep, get_project_member_dep
from src.schemas.character import CastingCreate, CastingDelete, CastingUser, CharacterResponse
from src.services.discord import DiscordService, get_discord_service

router = APIRouter()

@router.get("/{project_id}/characters", response_model=list[CharacterResponse])
async def list_project_characters(
    project_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> list[CharacterResponse]:
    """プロジェクトのキャラクター一覧（キャスティング情報含む）を取得.
    
    Args:
        project_id: プロジェクトID
        current_member: プロジェクトメンバー（権限チェック済み）
        db: DBセッション
        
    Returns:
        list[CharacterResponse]: キャラクターリスト
    """
    # プロジェクトの最新脚本を取得
    # 1プロジェクト1脚本制なので、リストの先頭または特定条件で取得
    result = await db.execute(select(Script).where(Script.project_id == project_id))
    scripts = result.scalars().all()

    if not scripts:
        return []

    # 最新の脚本（通常は1つのみ）
    script = scripts[0]

    # キャラクターとキャスティング情報を取得
    # User情報も一緒にロードする
    result = await db.execute(
        select(Character)
        .where(Character.script_id == script.id)
        .options(
            selectinload(Character.castings).selectinload(CharacterCasting.user)
        )
    )
    characters = result.scalars().all()

    # プロジェクトメンバー情報を取得して、user_id -> display_name のマップを作成
    member_result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    members = member_result.scalars().all()
    display_name_map = {m.user_id: m.display_name for m in members}

    response = []
    for char in characters:
        castings = []
        for cast in char.castings:
            castings.append(CastingUser(
                user_id=cast.user.id,
                discord_username=cast.user.discord_username,
                display_name=display_name_map.get(cast.user.id),
                cast_name=cast.cast_name
            ))

        response.append(CharacterResponse(
            id=char.id,
            name=char.name,
            castings=castings
        ))

    return response


@router.post("/{project_id}/characters/{character_id}/cast", response_model=list[CastingUser])
async def add_casting(
    project_id: UUID,
    character_id: UUID,
    casting_data: CastingCreate,
    background_tasks: BackgroundTasks,
    editor_member: ProjectMember = Depends(get_project_editor_dep), # 編集権限以上
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> list[CastingUser]:
    """キャラクターにキャストを追加.
    
    Args:
        project_id: プロジェクトID
        character_id: キャラクターID
        casting_data: キャスティングデータ
        editor_member: 実行者（編集者以上）
        db: DBセッション
        
    Returns:
        list[CastingUser]: 更新後のキャストリスト
    """
    # キャラクターの存在確認（かつプロジェクトに属しているか）
    # Character -> Script -> Project の整合性チェックが必要
    result = await db.execute(
        select(Character).join(Script).where(
            Character.id == character_id,
            Script.project_id == project_id
        )
    )
    character = result.scalar_one_or_none()

    if character is None:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません（または別プロジェクトのキャラクターです）")

    # ユーザー（キャスト対象）の存在確認
    # プロジェクトメンバーであるべきか？ -> 基本的にはYesだが、UserテーブルにあればOKとするか、
    # あるいはProjectMemberであることを強制するか。
    # 通常はプロジェクトメンバーから選ぶので、メンバーであることを確認するのが安全。
    result = await db.execute(
        select(User).join(ProjectMember).where(
            User.id == casting_data.user_id,
            ProjectMember.project_id == project_id
        )
    )
    target_user = result.scalar_one_or_none()

    if target_user is None:
        raise HTTPException(status_code=400, detail="指定されたユーザーはこのプロジェクトのメンバーではありません")

    # 重複チェック（同じキャラに同じユーザーを二重登録は不可）
    # CharacterCastingテーブルの一意制約はないが（キャスト名を変えれば複数登録可？）、通常は1キャラ1ユーザー1回。
    # ここでは重複を防ぐ。
    result = await db.execute(
        select(CharacterCasting).where(
            CharacterCasting.character_id == character_id,
            CharacterCasting.user_id == casting_data.user_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="このユーザーは既にこのキャラクターに配役されています")

    target_username = target_user.discord_username

    # 追加
    new_casting = CharacterCasting(
        character_id=character_id,
        user_id=casting_data.user_id,
        cast_name=casting_data.cast_name
    )
    db.add(new_casting)

    # 監査ログ
    audit = AuditLog(
        event="casting.add",
        user_id=editor_member.user_id,
        project_id=project_id,
        details=f"Assigned {target_user.discord_username} to {character.name}",
    )
    db.add(audit)

    await db.commit()

    # 更新後のリストを返すためにリフレッシュ
    # キャラクタを再取得してリレーションをロード
    result = await db.execute(
        select(Character)
        .where(Character.id == character_id)
        .options(
            selectinload(Character.castings).selectinload(CharacterCasting.user)
        )
    )
    character = result.scalar_one()

    # 通知
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"🎭 **配役決定**\nプロジェクト: {project.name}\nキャラクター: {character.name}\nキャスト: {target_username}",
        webhook_url=project.discord_webhook_url,
    )

    return [
        CastingUser(
            user_id=c.user.id,
            discord_username=c.user.discord_username,
            cast_name=c.cast_name
        ) for c in character.castings
    ]


@router.delete("/{project_id}/characters/{character_id}/cast", response_model=list[CastingUser])
async def remove_casting(
    project_id: UUID,
    character_id: UUID,
    delete_data: CastingDelete,
    background_tasks: BackgroundTasks,
    editor_member: ProjectMember = Depends(get_project_editor_dep), # 編集権限以上
    db: AsyncSession = Depends(get_db),
    discord_service: DiscordService = Depends(get_discord_service),
) -> list[CastingUser]:
    """配役を解除.
    
    Args:
        project_id: プロジェクトID
        character_id: キャラクターID
        delete_data: 解除データ（ユーザーID指定）
        editor_member: 実行者
        db: DBセッション
        
    Returns:
        list[CastingUser]: 更新後のキャストリスト
    """
    # キャラクター確認
    result = await db.execute(
        select(Character).join(Script).where(
            Character.id == character_id,
            Script.project_id == project_id
        )
    )
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    # 該当のキャスティングレコードを検索
    result = await db.execute(
        select(CharacterCasting).where(
            CharacterCasting.character_id == character_id,
            CharacterCasting.user_id == delete_data.user_id
        )
    )
    casting = result.scalar_one_or_none()

    if casting is None:
        raise HTTPException(status_code=404, detail="指定された配役が見つかりません")

    # ユーザー名取得（通知用）
    user_name = "Unknown"
    user_res = await db.execute(select(User.discord_username).where(User.id == delete_data.user_id))
    u = user_res.scalar_one_or_none()
    if u:
        user_name = u

    # 削除
    await db.delete(casting)

    # 監査ログ
    audit = AuditLog(
        event="casting.remove",
        user_id=editor_member.user_id,
        project_id=project_id,
        details=f"Removed {user_name} from {character.name}",
    )
    db.add(audit)

    await db.commit()

    # 更新後のリスト
    result = await db.execute(
        select(Character)
        .where(Character.id == character_id)
        .options(
            selectinload(Character.castings).selectinload(CharacterCasting.user)
        )
    )
    character = result.scalar_one()

    # 通知
    project = await db.get(TheaterProject, project_id)
    background_tasks.add_task(
        discord_service.send_notification,
        content=f"🚫 **配役解除**\nプロジェクト: {project.name}\nキャラクター: {character.name}\n対象: {user_name}",
        webhook_url=project.discord_webhook_url,
    )

    return [
        CastingUser(
            user_id=c.user.id,
            discord_username=c.user.discord_username,
            cast_name=c.cast_name
        ) for c in character.castings
    ]
