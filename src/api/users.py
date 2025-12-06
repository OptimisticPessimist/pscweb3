"""ユーザーAPIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import get_current_user
from src.db import get_db
from src.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """現在のユーザー情報を取得.

    Args:
        authorization: Authorization header (Bearer <token>)
        db: データベースセッション

    Returns:
        UserResponse: ユーザー情報

    Raises:
        HTTPException: 認証エラー
    """
    if not authorization.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    token = authorization.split(" ")[1]
    
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="無効なトークンです")

    return UserResponse.model_validate(user)
