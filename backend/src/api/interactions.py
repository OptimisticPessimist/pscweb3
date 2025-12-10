"""インタラクションAPIエンドポイント."""


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

# Discord インタラクションタイプ
INTERACTION_TYPE_PING = 1
INTERACTION_TYPE_APPLICATION_COMMAND = 2
INTERACTION_TYPE_MESSAGE_COMPONENT = 3

# レスポンスタイプ
RESPONSE_TYPE_PONG = 1
RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE = 4
RESPONSE_TYPE_DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
RESPONSE_TYPE_DEFERRED_UPDATE_MESSAGE = 6
RESPONSE_TYPE_UPDATE_MESSAGE = 7

class InteractionData(BaseModel):
    """Discordインタラクションのデータ部分."""
    
    custom_id: str | None = None
    component_type: int | None = None

class InteractionUser(BaseModel):
    """Discordインタラクションのユーザー情報."""
    
    id: str
    username: str
    discriminator: str

class InteractionMember(BaseModel):
    """Discordインタラクションのメンバー情報."""
    
    user: InteractionUser | None = None

class Interaction(BaseModel):
    """Discordインタラクション全体のモデル."""
    
    type: int
    token: str
    data: InteractionData | None = None
    member: InteractionMember | None = None # サーバーのみ
    user: InteractionUser | None = None # DMのみ
    message: dict | None = None

async def verify_signature(request: Request):
    """Discord署名ヘッダーを検証する."""
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="署名ヘッダーがありません")

    body = await request.body()

    try:
        verify_key = VerifyKey(bytes.fromhex(settings.discord_public_key or ""))
        verify_key.verify(f"{timestamp}".encode() + body, bytes.fromhex(signature))
    except (BadSignatureError, ValueError):
        raise HTTPException(status_code=401, detail="無効な署名です")

@router.post("/discord/interactions")
async def interaction_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Discordインタラクション（Webhooks）を処理する."""
    # 署名検証
    if not settings.discord_public_key:
        logger.error("Discord公開鍵が設定されていません")
        raise HTTPException(status_code=500, detail="サーバー設定エラー")

    await verify_signature(request)

    # リクエスト本文をパース
    try:
        payload = await request.json()
        interaction = Interaction(**payload)
    except Exception as e:
        logger.error("インタラクションのパースに失敗しました", error=str(e))
        raise HTTPException(status_code=400, detail="無効なJSONです")

    # PINGを処理
    if interaction.type == INTERACTION_TYPE_PING:
        return {"type": RESPONSE_TYPE_PONG}

    # ボタンクリックを処理（メッセージコンポーネント）
    if interaction.type == INTERACTION_TYPE_MESSAGE_COMPONENT:
        return await handle_button_interaction(interaction, db)

    return {"type": RESPONSE_TYPE_PONG} # フォールバック

async def handle_button_interaction(interaction: Interaction, db: AsyncSession):
    """ボタンクリックを処理する."""
    if not interaction.data or not interaction.data.custom_id:
        return {"type": RESPONSE_TYPE_UPDATE_MESSAGE}

    custom_id = interaction.data.custom_id
    # フォーマット: attendance:{event_id}:{status}
    parts = custom_id.split(":")

    if len(parts) != 3 or parts[0] != "attendance":
        # 未知のインタラクション
        return {"type": RESPONSE_TYPE_UPDATE_MESSAGE}

    event_id_str = parts[1]
    status = parts[2] # "ok", "ng", "pending"

    # DiscordユーザーIDを取得
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

    # DB内のユーザーを確認
    # Discord IDでUserを検索し、AttendanceTargetを探す必要がある
    # 注意: AttendanceTargetはUser.id（UUID）にリンクし、discord_idではない

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

    # ターゲットを更新
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
        # 対象ではない？動的に追加する可能性もあるが、今はエラー表示
        return {
            "type": RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "⚠️ あなたはこのイベントの対象者ではありません。",
                "flags": 64 # Ephemeral
            }
        }

    # ステータスを更新
    target.status = status
    await db.commit()

    logger.info("出席確認ステータスを更新しました", user_id=user.id, event_id=event_id, status=status)

    # ステータスメッセージ
    status_text = "参加" if status == "ok" else "不参加" if status == "ng" else "保留"
    return {
        "type": RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "content": f"✅ ステータスを「**{status_text}**」に更新しました。",
            "flags": 64 # Ephemeral
        }
    }
