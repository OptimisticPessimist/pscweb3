"""JWT認証ユーティリティのテスト."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import create_access_token, get_current_user
from src.db.models import User


@pytest.mark.asyncio
async def test_create_access_token(test_user: User) -> None:
    """JWTトークン生成のテスト."""
    # Arrange & Act
    token = create_access_token({"sub": str(test_user.id)})

    # Assert
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_get_current_user_valid_token(db: AsyncSession, test_user: User) -> None:
    """有効なトークンでユーザー取得のテスト."""
    # Arrange
    token = create_access_token({"sub": str(test_user.id)})

    # Act
    user = await get_current_user(token, db)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.discord_id == test_user.discord_id


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db: AsyncSession) -> None:
    """無効なトークンでユーザー取得のテスト."""
    # Arrange
    invalid_token = "invalid_token_string"

    # Act
    user = await get_current_user(invalid_token, db)

    # Assert
    assert user is None
