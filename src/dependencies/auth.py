from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user_dep(
    auth_token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI Depends用 ユーザー取得関数."""
    return await get_current_user(auth_token, db)


async def get_optional_current_user_dep(
    auth_token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """FastAPI Depends用 任意ユーザー取得関数."""
    # OAuth2PasswordBearerはトークンがないと401を出すので、Optionalにするなら修正が必要
    # しかし今回は簡易的に必須として扱うか、あるいはHeaderを使う手もある
    # ここでは既存のロジックに合わせて、Token取得を試みる
    try:
        if not auth_token:
            return None
        return await get_current_user(auth_token, db)
    except Exception:
        return None
