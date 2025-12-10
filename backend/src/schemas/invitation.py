from datetime import datetime

from pydantic import BaseModel, Field


class InvitationCreate(BaseModel):
    """招待作成リクエスト。"""
    max_uses: int | None = Field(None, gt=0)  # Noneなら無制限、指定する場合は1以上
    expires_in_hours: int = 24 * 7  # デフォルト1週間

class InvitationResponse(BaseModel):
    """招待情報レスポンス。"""
    model_config = {"from_attributes": True}

    token: str
    project_id: int
    project_name: str
    created_by: str  # 作成者名
    expires_at: datetime
    max_uses: int | None
    used_count: int

class InvitationAcceptResponse(BaseModel):
    """招待受諾レスポンス。"""
    project_id: int
    project_name: str
    message: str
