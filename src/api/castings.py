"""キャスティング管理APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import Character, CharacterCasting, ProjectMember, Script, User
from src.schemas.casting import (
    CharacterCastingCreate,
    CharacterCastingResponse,
    ScriptCastingResponse,
)

router = APIRouter()


@router.post("/characters/{character_id}/casting", response_model=CharacterCastingResponse)
async def assign_character_casting(
    character_id: int,
    casting_data: CharacterCastingCreate,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> CharacterCastingResponse:
    """登場人物にユーザーをキャスティング.

    Args:
        character_id: 登場人物ID
        casting_data: キャスティングデータ
        token: JWT トークン
        db: データベースセッション

    Returns:
        CharacterCastingResponse: キャスティング情報

    Raises:
        HTTPException: 認証エラー、権限エラー、または登場人物が見つからない
    """
    # 認証チェック
    current_user = await get_current_user(token, db)
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 登場人物取得
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=404, detail="登場人物が見つかりません")

    # 脚本とプロジェクトを取得
    result = await db.execute(
        select(Script).where(Script.id == character.script_id)
    )
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="キャスティングの権限がありません")

    # キャスト対象ユーザーを取得
    result = await db.execute(select(User).where(User.id == casting_data.user_id))
    cast_user = result.scalar_one_or_none()
    if cast_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # キャスティング作成
    casting = CharacterCasting(
        character_id=character_id,
        user_id=casting_data.user_id,
        cast_name=casting_data.cast_name,
    )
    db.add(casting)
    await db.commit()
    await db.refresh(casting)

    return CharacterCastingResponse(
        id=casting.id,
        character_id=character.id,
        character_name=character.name,
        user_id=cast_user.id,
        user_name=cast_user.discord_username,
        cast_name=casting.cast_name,
    )


@router.get("/scripts/{script_id}/castings", response_model=ScriptCastingResponse)
async def list_script_castings(
    script_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> ScriptCastingResponse:
    """脚本のキャスティング一覧を取得.

    Args:
        script_id: 脚本ID
        token: JWT トークン
        db: データベースセッション

    Returns:
        ScriptCastingResponse: キャスティング一覧

    Raises:
        HTTPException: 認証エラーまたは権限エラー
    """
    # 認証チェック
    current_user = await get_current_user(token, db)
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # 脚本取得
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if script is None:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="このプロジェクトへのアクセス権がありません")

    # キャスティング一覧取得
    result = await db.execute(
        select(CharacterCasting)
        .join(Character)
        .where(Character.script_id == script_id)
    )
    castings = result.scalars().all()

    casting_responses = []
    for casting in castings:
        # Characterとリレーションを再取得
        result = await db.execute(
            select(Character).where(Character.id == casting.character_id)
        )
        character = result.scalar_one()

        result = await db.execute(select(User).where(User.id == casting.user_id))
        user = result.scalar_one()

        casting_responses.append(
            CharacterCastingResponse(
                id=casting.id,
                character_id=character.id,
                character_name=character.name,
                user_id=user.id,
                user_name=user.discord_username,
                cast_name=casting.cast_name,
            )
        )

    return ScriptCastingResponse(
        script_id=script.id,
        script_title=script.title,
        castings=casting_responses,
    )


@router.delete("/castings/{casting_id}")
async def delete_character_casting(
    casting_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """キャスティングを削除.

    Args:
        casting_id: キャスティングID
        token: JWT トークン
        db: データベースセッション

    Returns:
        dict: 成功メッセージ

    Raises:
        HTTPException: 認証エラー、権限エラー、またはキャスティングが見つからない
    """
    # 認証チェック
    current_user = await get_current_user(token, db)
    if current_user is None:
        raise HTTPException(status_code=401, detail="認証が必要です")

    # キャスティング取得
    result = await db.execute(
        select(CharacterCasting).where(CharacterCasting.id == casting_id)
    )
    casting = result.scalar_one_or_none()
    if casting is None:
        raise HTTPException(status_code=404, detail="キャスティングが見つかりません")

    # 登場人物と脚本を取得
    result = await db.execute(
        select(Character).where(Character.id == casting.character_id)
    )
    character = result.scalar_one()

    result = await db.execute(select(Script).where(Script.id == character.script_id))
    script = result.scalar_one()

    # プロジェクトメンバーシップチェック
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == script.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(status_code=403, detail="キャスティング削除の権限がありません")

    # 削除
    await db.delete(casting)
    await db.commit()

    return {"message": "キャスティングを削除しました"}
