"""認証関連の依存性注入."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import User


async def get_current_user_dep(
    authorization: str | None = Header(None, alias="Authorization", description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI Depends用 ユーザー取得関数."""
    if not authorization or not authorization.startswith("Bearer "):
        # 401を上げるか、Noneを返すか。依存元がチェックしているのでNoneでもよいが、
        # users.pyと同様のロジックにするならここでチェックしてもよい。
        # ここではNoneを返して依存元(projects.pyなど)で401にさせる
        return None

    token = authorization.split(" ")[1]
    return await get_current_user(token, db)


async def get_optional_current_user_dep(
    authorization: str | None = Header(None, alias="Authorization", description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI Depends用 任意ユーザー取得関数."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        return await get_current_user(token, db)
    except Exception:
        return None
