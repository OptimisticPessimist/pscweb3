"""Discord Interactions API endpoints."""


from fastapi import APIRouter, Depends, HTTPException, Request
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from src.config import settings
from src.db import get_db
from src.db.models import AttendanceTarget

router = APIRouter()
logger = get_logger(__name__)

# Discord Interaction Types
INTERACTION_TYPE_PING = 1
INTERACTION_TYPE_APPLICATION_COMMAND = 2
INTERACTION_TYPE_MESSAGE_COMPONENT = 3

# Response Types
RESPONSE_TYPE_PONG = 1
RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE = 4
RESPONSE_TYPE_DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
RESPONSE_TYPE_DEFERRED_UPDATE_MESSAGE = 6
RESPONSE_TYPE_UPDATE_MESSAGE = 7

class InteractionData(BaseModel):
    custom_id: str | None = None
    component_type: int | None = None

class InteractionUser(BaseModel):
    id: str
    username: str
    discriminator: str

class InteractionMember(BaseModel):
    user: InteractionUser | None = None

class Interaction(BaseModel):
    type: int
    token: str
    data: InteractionData | None = None
    member: InteractionMember | None = None # Sever-only
    user: InteractionUser | None = None # DM-only
    message: dict | None = None

async def verify_signature(request: Request):
    """Verify Discord signature headers."""
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signature headers")

    body = await request.body()

    try:
        verify_key = VerifyKey(bytes.fromhex(settings.discord_public_key or ""))
        verify_key.verify(f"{timestamp}".encode() + body, bytes.fromhex(signature))
    except (BadSignatureError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/discord/interactions")
async def interaction_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Discord Interactions (Webhooks)."""
    # Verify Signature
    if not settings.discord_public_key:
        logger.error("Discord Public Key not configured")
        raise HTTPException(status_code=500, detail="Server configuration error")

    await verify_signature(request)

    # Parse Body
    try:
        payload = await request.json()
        interaction = Interaction(**payload)
    except Exception as e:
        logger.error("Failed to parse interaction", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle PING
    if interaction.type == INTERACTION_TYPE_PING:
        return {"type": RESPONSE_TYPE_PONG}

    # Handle Button Click (Message Component)
    if interaction.type == INTERACTION_TYPE_MESSAGE_COMPONENT:
        return await handle_button_interaction(interaction, db)

    return {"type": RESPONSE_TYPE_PONG} # Fallback

async def handle_button_interaction(interaction: Interaction, db: AsyncSession):
    """Handle button clicks."""
    if not interaction.data or not interaction.data.custom_id:
        return {"type": RESPONSE_TYPE_UPDATE_MESSAGE}

    custom_id = interaction.data.custom_id
    # Format: attendance:{event_id}:{status}
    parts = custom_id.split(":")

    if len(parts) != 3 or parts[0] != "attendance":
        # Unknown interaction
        return {"type": RESPONSE_TYPE_UPDATE_MESSAGE}

    event_id_str = parts[1]
    status = parts[2] # "ok", "ng", "pending"

    # Get Discord User ID
    discord_user_id = None
    if interaction.member and interaction.member.user:
        discord_user_id = interaction.member.user.id
    elif interaction.user:
        discord_user_id = interaction.user.id

    if not discord_user_id:
        return {
            "type": RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "⚠️ ユーザー情報を取得できませんでした。",
                "flags": 64 # Ephemeral
            }
        }

    # Verify User in DB
    # We need to find the User by discord_id and then find the AttendanceTarget
    # But wait, AttendanceTarget links to User.id (UUID), not discord_id.
    # So we must verify the user exists in our DB.

    from src.db.models import User
    stmt = select(User).where(User.discord_id == discord_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
         return {
            "type": RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "⚠️ このシステムに登録されていないユーザーです。",
                "flags": 64 # Ephemeral
            }
        }

    # Update Target
    from uuid import UUID
    try:
        event_id = UUID(event_id_str)
    except ValueError:
         return {"type": RESPONSE_TYPE_UPDATE_MESSAGE}

    stmt = select(AttendanceTarget).where(
        AttendanceTarget.event_id == event_id,
        AttendanceTarget.user_id == user.id
    )
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()

    if not target:
        # Not a target? Maybe add them dynamically?
        # For now, show error.
        return {
            "type": RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "⚠️ あなたはこのイベントの対象者ではありません。",
                "flags": 64 # Ephemeral
            }
        }

    # Update Status
    target.status = status
    await db.commit()

    logger.info("Updated attendance status", user_id=user.id, event_id=event_id, status=status)

    # Status Message
    status_text = "参加" if status == "ok" else "不参加" if status == "ng" else "保留"
    return {
        "type": RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "content": f"✅ ステータスを「**{status_text}**」に更新しました。",
            "flags": 64 # Ephemeral
        }
    }
