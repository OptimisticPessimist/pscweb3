"""キャスティングAPIの統合テスト."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Character, Script, TheaterProject, User
from src.main import app


@pytest.mark.asyncio
async def test_assign_casting(db: AsyncSession, test_project: TheaterProject, test_user: User) -> None:
    """キャスト割り当てのテスト."""
    # Arrange: 脚本と登場人物を作成
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="テスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.flush()

    character = Character(
        script_id=script.id,
        name="主人公",
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)

    # JWTトークンを取得（簡易版：実際にはauth.jwtから生成）
    from src.auth.jwt import create_access_token
    token = create_access_token({"sub": str(test_user.discord_id)})

    # Act: キャスト割り当てAPI呼び出し
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/scripts/characters/{character.id}/casting?token={token}",
            json={"user_id": test_user.id, "cast_name": "Aキャスト"},
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["character_id"] == character.id
    assert data["user_id"] == test_user.id
    assert data["cast_name"] == "Aキャスト"
