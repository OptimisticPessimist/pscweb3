"""JWT認証ユーティリティ."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import User


def create_access_token(data: dict[str, str | int]) -> str:
    """JWTアクセストークンを生成.

    Args:
        data: トークンに含めるデータ

    Returns:
        str: JWT トークン
    """
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(token: str, db: AsyncSession) -> User | None:
    """JWTトークンから現在のユーザーを取得.

    Args:
        token: JWT トークン
        db: データベースセッション

    Returns:
        User | None: ユーザーオブジェクト、無効な場合はNone
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id_str: str | None = payload.get("sub")
        
        if user_id_str is None:
            return None
        
        user_id = int(user_id_str)
        
    except (JWTError, ValueError):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()







