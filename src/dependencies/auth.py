from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import User

async def get_current_user_dep(
    auth_token: str = Query(..., alias="token", description="JWT Token"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI Depends用 ユーザー取得関数."""
    return await get_current_user(auth_token, db)


async def get_optional_current_user_dep(
    auth_token: str | None = Query(None, alias="token", description="JWT Token (Optional)"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI Depends用 任意ユーザー取得関数."""
    if not auth_token:
        return None
    return await get_current_user(auth_token, db)
