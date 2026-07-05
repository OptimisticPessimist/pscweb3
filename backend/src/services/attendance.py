"""出席確認サービス."""

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
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

JST = timezone(timedelta(hours=9))
ATTENDANCE_STATUSES = {"ok", "ng", "pending"}


def to_utc(dt: datetime | None) -> datetime | None:
    """naive datetime は UTC とみなし、aware datetime は UTC へ変換する.

    `.replace(tzinfo=UTC)` は aware な非UTC日時（例: +09:00）を壊すため、
    タイムスタンプ計算前の正規化には必ずこちらを使う。
    """
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def normalize_attendance_status(status: str | None) -> str:
    """出欠確認のDBステータスとして保存できる値へ正規化する."""
    return status if status in ATTENDANCE_STATUSES else "pending"


def _rehearsal_event_conditions(
    rehearsal_id: uuid.UUID,
    old_schedule_date: datetime | None,
):
    """稽古に紐づく出欠イベントの照合条件を構築する.

    rehearsal_id で直接紐づくものに加え、rehearsal_id 未設定の既存データは
    旧稽古日時との一致で照合する（フロントエンドの照合ロジックと同じ規則）。
    """
    conditions = [AttendanceEvent.rehearsal_id == rehearsal_id]
    old_dt = to_utc(old_schedule_date)
    if old_dt is not None:
        conditions.append(
            and_(
                AttendanceEvent.rehearsal_id.is_(None),
                AttendanceEvent.schedule_date == old_dt,
            )
        )
    return or_(*conditions)


async def sync_rehearsal_attendance_events(
    db: AsyncSession,
    rehearsal_id: uuid.UUID,
    project_id: uuid.UUID,
    old_schedule_date: datetime | None,
    new_schedule_date: datetime | None = None,
    target_user_ids: set[uuid.UUID] | None = None,
) -> int:
    """稽古の変更内容を、紐づく未完了の出欠確認イベントへ同期する.

    - 日時変更時: schedule_date を更新し、回答期限を同じ差分だけ移動、
      リマインダー送信済みフラグをリセットする。タイトルに旧日時(JST)表記が
      含まれる場合は新日時へ置換する。
    - 対象者変更時 (target_user_ids is not None): 既存の回答は保持したまま、
      追加されたメンバーを pending で追加し、対象から外れたメンバーを削除する。
      （作成時と同様、Discord連携済みユーザーのみを対象とする）
    - rehearsal_id 未設定の既存イベントには rehearsal_id を補完する。

    呼び出し元で commit すること。

    Returns:
        int: 同期した出欠イベント数
    """
    stmt = (
        select(AttendanceEvent)
        .where(
            AttendanceEvent.project_id == project_id,
            AttendanceEvent.completed == False,  # noqa: E712
            _rehearsal_event_conditions(rehearsal_id, old_schedule_date),
        )
        .options(selectinload(AttendanceEvent.targets))
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    if not events:
        return 0

    desired_ids: set[uuid.UUID] | None = None
    if target_user_ids is not None:
        if target_user_ids:
            users_result = await db.execute(
                select(User.id).where(
                    User.id.in_(target_user_ids), User.discord_id.isnot(None)
                )
            )
            desired_ids = set(users_result.scalars().all())
        else:
            desired_ids = set()

    new_dt = to_utc(new_schedule_date)

    for event in events:
        # rehearsal_id 未設定の既存データを補完
        event.rehearsal_id = rehearsal_id

        # 稽古日時の同期
        current_dt = to_utc(event.schedule_date)
        if new_dt is not None and current_dt != new_dt:
            if current_dt is not None:
                delta = new_dt - current_dt
                if event.deadline is not None:
                    event.deadline = to_utc(event.deadline) + delta
                # タイトル中の旧日時表記(JST)を新日時へ置換
                old_label = current_dt.astimezone(JST).strftime("%m/%d %H:%M")
                new_label = new_dt.astimezone(JST).strftime("%m/%d %H:%M")
                if event.title and old_label in event.title:
                    event.title = event.title.replace(old_label, new_label)
            event.schedule_date = new_dt
            # 新しい日時基準でリマインダーを再送できるようリセット
            event.reminder_1_sent_at = None
            event.reminder_2_sent_at = None
            event.reminder_3_sent_at = None
            logger.info(
                "attendance_event_schedule_synced",
                event_id=str(event.id),
                rehearsal_id=str(rehearsal_id),
                new_schedule_date=new_dt.isoformat(),
            )

        # 対象者の同期（既存回答は保持）
        if desired_ids is not None:
            existing = {t.user_id: t for t in event.targets}
            for user_id, target in existing.items():
                if user_id not in desired_ids:
                    await db.delete(target)
            for user_id in desired_ids - existing.keys():
                db.add(
                    AttendanceTarget(event_id=event.id, user_id=user_id, status="pending")
                )
            logger.info(
                "attendance_event_targets_synced",
                event_id=str(event.id),
                rehearsal_id=str(rehearsal_id),
                target_count=len(desired_ids),
            )

    return len(events)


async def complete_rehearsal_attendance_events(
    db: AsyncSession,
    rehearsal_id: uuid.UUID,
    project_id: uuid.UUID,
    schedule_date: datetime | None,
) -> int:
    """稽古削除時に、紐づく出欠確認イベントを完了扱いにしてリマインダーを停止する.

    呼び出し元で commit すること。

    Returns:
        int: 完了扱いにした出欠イベント数
    """
    stmt = select(AttendanceEvent).where(
        AttendanceEvent.project_id == project_id,
        AttendanceEvent.completed == False,  # noqa: E712
        _rehearsal_event_conditions(rehearsal_id, schedule_date),
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    for event in events:
        event.completed = True
        logger.info(
            "attendance_event_completed_by_rehearsal_delete",
            event_id=str(event.id),
            rehearsal_id=str(rehearsal_id),
        )

    return len(events)


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
        location: str | None = None,
        description: str | None = None,
        target_user_ids: list[uuid.UUID] | None = None,
        rehearsal_id: uuid.UUID | None = None,
        initial_status_by_user_id: Mapping[uuid.UUID, str] | None = None,
    ) -> AttendanceEvent | None:
        """出席確認イベントを作成し、Disocrdに通知を送信する.

        Args:
            project: プロジェクトモデル
            title: イベントタイトル
            deadline: 回答期限
            schedule_date: イベント日時
            location: 場所（オプション）
            description: 説明（オプション）
            target_user_ids: 対象ユーザーIDのリスト（Noneの場合は全メンバー）
            rehearsal_id: 紐付く稽古ID（稽古由来の出欠確認の場合）
            initial_status_by_user_id: 対象者ごとの初期ステータス

        Returns:
            Optional[AttendanceEvent]: 作成されたイベント、失敗時はNone
        """
        if not project.discord_channel_id:
            logger.warning("Discord Channel ID not set for project", project_id=project.id)
            return None

        logger.info(
            f"Creating attendance for project {project.name}, channel {project.discord_channel_id}"
        )

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
        deadline_ts = int(to_utc(deadline).timestamp())
        schedule_ts = int(to_utc(schedule_date).timestamp())
        deadline_str = f"<t:{deadline_ts}:f>"
        schedule_str = f"<t:{schedule_ts}:f>"

        message_content = f"**【出欠確認】{title}**\n日時: {schedule_str}\n期限: {deadline_str}\n"

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
                "type": 1,  # Action Row
                "components": [
                    {
                        "type": 2,  # Button
                        "label": "参加",
                        "custom_id": f"attendance:{event_id}:ok",
                        "style": 3,  # Success
                    },
                    {
                        "type": 2,
                        "style": 4,  # Danger
                        "label": "不参加",
                        "custom_id": f"attendance:{event_id}:ng",
                    },
                    {
                        "type": 2,
                        "style": 2,  # Secondary (Grey)
                        "label": "保留",
                        "custom_id": f"attendance:{event_id}:pending",
                    },
                ],
            }
        ]

        # Discord送信
        discord_resp = await self.discord_service.send_channel_message(
            channel_id=project.discord_channel_id, content=message_content, components=components
        )

        if not discord_resp or "id" not in discord_resp:
            logger.error("Failed to send Discord message for attendance", project_id=project.id)
            return None

        # DB保存
        attendance_event = AttendanceEvent(
            id=event_id,
            project_id=project.id,
            rehearsal_id=rehearsal_id,
            message_id=discord_resp["id"],
            channel_id=project.discord_channel_id,
            title=title,
            schedule_date=to_utc(schedule_date),
            deadline=to_utc(deadline),
            completed=False,
        )
        self.db.add(attendance_event)
        await self.db.flush()

        for user in valid_users:
            initial_status = normalize_attendance_status(
                initial_status_by_user_id.get(user.id) if initial_status_by_user_id else None
            )
            target = AttendanceTarget(
                event_id=attendance_event.id, user_id=user.id, status=initial_status
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
