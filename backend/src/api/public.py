"""公開APIエンドポイント."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import Script, Character, CharacterCasting, Scene, Line
from src.schemas.script import ScriptResponse

router = APIRouter()

@router.get("/scripts/{script_id}", response_model=ScriptResponse)
async def get_public_script(
    script_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ScriptResponse:
    """公開されている脚本の詳細を取得（認証不要）.
    
    Args:
        script_id: 脚本ID
        db: データベースセッション

    Returns:
        ScriptResponse: 脚本詳細

    Raises:
        HTTPException: 脚本が見つからない、または公開されていない場合
    """
    # 脚本取得（公開フラグチェック付き）
    stmt = (
        select(Script)
        .where(Script.id == script_id)
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
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="脚本が見つかりません")

    if not script.is_public:
        raise HTTPException(status_code=403, detail="この脚本は公開されていません")

    return ScriptResponse.model_validate(script)
