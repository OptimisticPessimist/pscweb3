"""キャスティングAPIの統合テスト."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

"""キャスティングAPIの統合テスト."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Character, Script, TheaterProject, User
from src.main import app


@pytest.mark.asyncio
async def test_assign_casting(
    db: AsyncSession, test_project: TheaterProject, test_user: User, client: AsyncClient
) -> None:
    """キャスト割り当てのテスト."""
    
    # Arrange: 脚本と登場人物を作成
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="テスト脚本",
        content="Title: テスト脚本\n\nINT. シーン - DAY\n\n主人公\nセリフ。",
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

    # JWTトークンを取得
    from src.auth.jwt import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    
    # Act: キャスト割り当てAPI呼び出し
    response = await client.post(
        f"/api/projects/{test_project.id}/characters/{character.id}/cast",
        json={"user_id": str(test_user.id), "cast_name": "Aキャスト"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Assert
    assert response.status_code == 200
    data_list = response.json()
    assert isinstance(data_list, list)
    
    # 割り当てたユーザーが含まれているか探す
    found = next((d for d in data_list if d["user_id"] == str(test_user.id)), None)
    assert found is not None
    assert found["cast_name"] == "Aキャスト"
