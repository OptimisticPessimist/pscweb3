"""依存性注入（dependencies）のテスト."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user_dep, get_optional_current_user_dep
from src.db.models import User


@pytest.mark.asyncio
async def test_get_current_user_dep_valid_token(
    test_user: User, test_user_token: str, db: AsyncSession
) -> None:
    """有効なトークンでユーザー取得の依存性注入テスト."""
    # Arrange
    authorization = f"Bearer {test_user_token}"
    
    # Act - 直接関数を呼び出して依存性をテスト
    from src.dependencies.auth import get_current_user_dep
    user = await get_current_user_dep(authorization=authorization, db=db)
    
    # Assert
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_get_current_user_dep_no_token(db: AsyncSession) -> None:
    """トークンなしでの依存性注入テスト."""
    # Act
    user = await get_current_user_dep(authorization=None, db=db)
    
    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_get_current_user_dep_invalid_format(db: AsyncSession) -> None:
    """無効なフォーマットのトークンでの依存性注入テスト."""
    # Arrange
    authorization = "InvalidFormat token"
    
    # Act
    user = await get_current_user_dep(authorization=authorization, db=db)
    
    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_get_optional_current_user_dep_valid_token(
    test_user: User, test_user_token: str, db: AsyncSession
) -> None:
    """有効なトークンでのオプショナルユーザー取得テスト."""
    # Arrange
    authorization = f"Bearer {test_user_token}"
    
    # Act
    user = await get_optional_current_user_dep(authorization=authorization, db=db)
    
    # Assert
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_get_optional_current_user_dep_no_token(db: AsyncSession) -> None:
    """トークンなしでのオプショナルユーザー取得テスト."""
    # Act
    user = await get_optional_current_user_dep(authorization=None, db=db)
    
    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_get_optional_current_user_dep_invalid_token(db: AsyncSession) -> None:
    """無効なトークンでのオプショナルユーザー取得テスト（エラーを吸収）."""
    # Arrange
    authorization = "Bearer invalid.token.here"
    
    # Act
    user = await get_optional_current_user_dep(authorization=authorization, db=db)
    
    # Assert
    # オプショナルなので、エラーではなくNoneを返すべき
    assert user is None
