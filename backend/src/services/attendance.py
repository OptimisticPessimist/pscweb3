"""出席確認サービス."""

from datetime import datetime, timedelta
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from src.db.models import (
    AttendanceEvent,
    AttendanceTarget,
    ProjectMember,
    TheaterProject,
    User,
)
from src.services.discord import DiscordService

logger = get_logger(__name__)


class AttendanceService:
    """出席確認イベントを管理するサービス."""

    def __init__(self, db: AsyncSession, discord_service: DiscordService) -> None:
        """初期化.

        Args:
            db: データベースセッション
            discord_service: Discordサービス
        """
        self.db = db
        self.discord_service = discord_service

    async def create_attendance_event(
        self,
        project: TheaterProject,
        title: str,
        deadline: datetime,
        schedule_date: datetime,
        location: Optional[str] = None,
        description: Optional[str] = None,
        target_user_ids: Optional[list[uuid.UUID]] = None,
    ) -> Optional[AttendanceEvent]:
        """出席確認イベントを作成し、Disocrdに通知を送信する.

        Args:
            project: プロジェクトモデル
            title: イベントタイトル
            deadline: 回答期限
            schedule_date: イベント日時
            location: 場所（オプション）
            description: 説明（オプション）
            target_user_ids: 対象ユーザーIDのリスト（Noneの場合は全メンバー）

        Returns:
            Optional[AttendanceEvent]: 作成されたイベント、失敗時はNone
        """
        if not project.discord_channel_id:
            logger.warning("Discord Channel ID not set for project", project_id=project.id)
            return None
            
        logger.info(f"Creating attendance for project {project.name}, channel {project.discord_channel_id}")

        valid_users = []
        if target_user_ids:
            # 指定されたユーザーを取得（discord_id所持者のみ）
            users_result = await self.db.execute(
                select(User).where(User.id.in_(target_user_ids), User.discord_id.isnot(None))
            )
            valid_users = users_result.scalars().all()
            logger.info(f"Found {len(valid_users)} valid discord users from specified targets")
        else:
            # メンバー全員を対象とする
            all_members_result = await self.db.execute(
                select(ProjectMember).where(ProjectMember.project_id == project.id)
            )
            all_members = all_members_result.scalars().all()
            all_target_ids = [m.user_id for m in all_members]
            
            # ユーザー取得（discord_id所持者のみ）
            users_result = await self.db.execute(
                select(User).where(User.id.in_(all_target_ids), User.discord_id.isnot(None))
            )
            valid_users = users_result.scalars().all()
            logger.info(f"Found {len(valid_users)} valid discord users from all members")

        if not valid_users:
            logger.info("No valid Discord users found for attendance check", project_id=project.id)
            return None

        # メンション作成
        mentions = [f"<@{u.discord_id}>" for u in valid_users]
        deadline_ts = int(deadline.replace(tzinfo=timezone.utc).timestamp())
        schedule_ts = int(schedule_date.replace(tzinfo=timezone.utc).timestamp())
        deadline_str = f"<t:{deadline_ts}:f>"
        schedule_str = f"<t:{schedule_ts}:f>"

        message_content = (
            f"**【出欠確認】{title}**\n"
            f"日時: {schedule_str}\n"
            f"期限: {deadline_str}\n"
        )
        
        if location:
            message_content += f"場所: {location}\n"
            
        message_content += f"対象: {' '.join(mentions)}\n\n"
        
        if description:
            message_content += f"{description}\n\n"
            
        message_content += "以下のボタンで出欠を登録してください。"

        # ボタンコンポーネント (Action Row)
        # 暫定的にDB保存前にIDが必要だが、event_idはまだない。
        # なので、message_idが返ってきてからupdateするか、UUIDを先に振るか。
        # UUIDはPython側で生成しているので、先に生成して使うのが良い。
        
        # UUID生成
        import uuid
        event_id = uuid.uuid4()
        
        components = [
            {
                "type": 1, # Action Row
                "components": [
                    {
                        "type": 2, # Button
                        "style": 1, # Primary (Blurple) -> 3 (Green) for OK?
                        "label": "参加",
                        "custom_id": f"attendance:{event_id}:ok",
                        "style": 3 # Success
                    },
                    {
                        "type": 2, 
                        "style": 4, # Danger
                        "label": "不参加",
                        "custom_id": f"attendance:{event_id}:ng"
                    },
                    {
                        "type": 2,
                        "style": 2, # Secondary (Grey)
                        "label": "保留",
                        "custom_id": f"attendance:{event_id}:pending"
                    }
                ]
            }
        ]

        # Discord送信
        discord_resp = await self.discord_service.send_channel_message(
            channel_id=project.discord_channel_id,
            content=message_content,
            components=components
        )

        if not discord_resp or "id" not in discord_resp:
            logger.error("Failed to send Discord message for attendance", project_id=project.id)
            return None

        # DB保存
        attendance_event = AttendanceEvent(
            id=event_id,
            project_id=project.id,
            message_id=discord_resp["id"],
            channel_id=project.discord_channel_id,
            title=title,
            schedule_date=schedule_date,
            deadline=deadline,
            completed=False
        )
        self.db.add(attendance_event)
        await self.db.flush()

        for user in valid_users:
            target = AttendanceTarget(
                event_id=attendance_event.id,
                user_id=user.id,
                status="pending"
            )
            self.db.add(target)

        await self.db.commit()
        await self.db.refresh(attendance_event)
        
        return attendance_event


def get_attendance_service(
    db: AsyncSession,
    discord_service: DiscordService,
) -> AttendanceService:
    """AttendanceServiceのインスタンスを取得."""
    return AttendanceService(db, discord_service)
