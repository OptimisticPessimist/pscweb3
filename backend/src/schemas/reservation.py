from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ReservationBase(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    count: int = Field(..., ge=1, le=4)
    referral_user_id: UUID | None = Field(default=None)
    milestone_id: UUID


class ReservationCreate(ReservationBase):
    pass


class ReservationCancel(BaseModel):
    reservation_id: UUID
    email: EmailStr


class ReservationUpdate(BaseModel):
    attended: bool


class ReservationResponse(ReservationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    attended: bool = False
    reminder_sent_at: datetime | None = None
    created_at: datetime

    # 関連情報
    milestone_title: str | None = None
    referral_name: str | None = None
