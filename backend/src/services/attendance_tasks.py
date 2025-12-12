"""定時実行タスク：出欠確認のリマインダー."""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db import async_session_maker
from src.db.models import AttendanceEvent, AttendanceTarget, User, TheaterProject
from src.services.discord import get_discord_service

logger = logging.getLogger(__name__)

async def check_deadlines() -> dict[str, int]:
    """期限切れで未完了のイベントをチェックし、リマインダーを送信する.

    Returns:
        dict[str, int]: 処理結果の統計
            - checked_events: チェックしたイベント数
            - reminders_sent: リマインダーを送信したイベント数
            - errors: エラー数
    """
    stats = {"checked_events": 0, "reminders_sent": 0, "errors": 0}
    
    async with async_session_maker() as db:
        now = datetime.now(timezone.utc)
        
        # 1. 期限切れ かつ 未完了 かつ リマインダー未送信 のイベントを取得
        stmt = (
            select(AttendanceEvent)
            .where(
                AttendanceEvent.deadline <= now,
                AttendanceEvent.completed == False,  # noqa: E712
                AttendanceEvent.reminder_sent_at.is_(None)
            )
            .options(
                selectinload(AttendanceEvent.targets).selectinload(AttendanceTarget.user),
                selectinload(AttendanceEvent.project)
            )
        )
        
        result = await db.execute(stmt)
        events = result.scalars().all()
        stats["checked_events"] = len(events)
        
        logger.info(f"Found {len(events)} expired events to check.")
        
        for event in events:
            try:
                # projectがロードできているか確認
                if not event.project:
                    logger.warning(f"Project not found for event {event.id}")
                    stats["errors"] += 1
                    continue
                    
                # 未回答(pending)のターゲットを抽出
                pending_targets = [t for t in event.targets if t.status == "pending"]
                
                if not pending_targets:
                    logger.info(f"No pending users for event {event.id}. Marking as reminded/skipped.")
                    # 対象者がいない場合もリマインダー送信済み（または送る必要なし）としてマーク
                    event.reminder_sent_at = now
                    continue
                
                # Discord通知ロジック
                # ユーザーIDリスト
                pending_user_ids = [t.user_id for t in pending_targets]
                
                # Reminder送信処理
                sent = await _send_reminder(event, pending_targets, event.project)
                
                # DB更新
                event.reminder_sent_at = now
                if sent:
                    stats["reminders_sent"] += 1
                
            except Exception as e:
                logger.error(f"Error processing event {event.id}: {e}", exc_info=True)
                stats["errors"] += 1
        
        # コミット
        await db.commit()
        
    return stats


async def _send_reminder(event: AttendanceEvent, pending_targets: list[AttendanceTarget], project: TheaterProject) -> bool:
    """Discordリマインダー送信.
    
    Returns:
        bool: 送信成功の場合True
    """
    if not project.discord_channel_id:
        logger.warning(f"No Discord channel ID for project {project.id}")
        return False

    # メンション作成のためDiscord IDが必要だが、AttendanceTarget.userはロード済み
    mentions = []
    for t in pending_targets:
        if t.user.discord_id:
            mentions.append(f"<@{t.user.discord_id}>")
    
    if not mentions:
        logger.info("No Discord users to mention.")
        return False

    deadline_str = event.deadline.strftime('%Y-%m-%d %H:%M')
    schedule_str = event.schedule_date.strftime('%Y-%m-%d %H:%M') if event.schedule_date else "未定"
    
    # メッセージ本文
    message_content = (
        f"**【自動リマインダー】回答期限が過ぎています**\n"
        f"イベント: **{event.title}**\n"
        f"日時: {schedule_str}\n"
        f"期限: {deadline_str}\n"
        f"未回答の方: {' '.join(mentions)}\n\n"
        f"回答をお願いします。"
    )
    
    discord_service = get_discord_service()
    await discord_service.send_channel_message(
        channel_id=project.discord_channel_id,
        content=message_content
    )
    logger.info(f"Sent reminder to {project.discord_channel_id} for event {event.id}")
    return True
