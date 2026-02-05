"""定時実行タスク：チケット予約のリマインダー."""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import async_session_maker
from src.db.models import Reservation, Milestone, TheaterProject
from src.services.email import email_service

logger = logging.getLogger(__name__)

async def check_todays_events(db: AsyncSession | None = None) -> dict[str, int]:
    """当日のイベントをチェックし、予約者にリマインダーメールを送信する.
    
    Returns:
        dict[str, int]: 処理結果の統計
            - checked_reservations: チェックした予約数
            - reminders_sent: リマインダーを送信した予約数
            - errors: エラー数
    """
    stats = {"checked_reservations": 0, "reminders_sent": 0, "errors": 0}
    
    if db is not None:
        return await _do_check_todays_events(db, stats)

    async with async_session_maker() as session:
        return await _do_check_todays_events(session, stats)

async def _do_check_todays_events(db: AsyncSession, stats: dict[str, int]) -> dict[str, int]:
    # JSTで当日の範囲を計算（00:00 - 23:59）
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    
    # JSTで当日の開始と終了をUTCに変換
    today_start_jst = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_jst = now_jst.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    today_start_utc = today_start_jst.astimezone(timezone.utc).replace(tzinfo=None)
    today_end_utc = today_end_jst.astimezone(timezone.utc).replace(tzinfo=None)
    
    # 1. 当日のマイルストーンを取得
    stmt = (
        select(Milestone)
        .where(
            Milestone.start_date >= today_start_utc,
            Milestone.start_date <= today_end_utc
        )
        .options(
            selectinload(Milestone.reservations),
            selectinload(Milestone.project)
        )
    )
    
    result = await db.execute(stmt)
    milestones = result.scalars().all()
    
    logger.info(f"Found {len(milestones)} events today.")
    
    for milestone in milestones:
        # 未送信の予約を抽出
        pending_reservations = [
            r for r in milestone.reservations 
            if r.reminder_sent_at is None
        ]
        
        stats["checked_reservations"] += len(pending_reservations)
        
        for reservation in pending_reservations:
            try:
                # プロジェクト情報取得
                project = milestone.project
                if not project:
                    logger.warning(f"Project not found for milestone {milestone.id}")
                    stats["errors"] += 1
                    continue
                
                # 日時をJSTに変換
                start_date_utc = milestone.start_date.replace(tzinfo=timezone.utc)
                start_date_jst = start_date_utc.astimezone(jst)
                date_str = start_date_jst.strftime("%Y/%m/%d %H:%M")
                
                # リマインダーメール送信
                sent = email_service.send_event_reminder(
                    to_email=reservation.email,
                    name=reservation.name,
                    milestone_title=milestone.title,
                    date_str=date_str,
                    count=reservation.count,
                    project_name=project.name,
                    location=milestone.location
                )
                
                if sent:
                    # 送信成功時、送信日時を記録
                    reservation.reminder_sent_at = datetime.now(timezone.utc)
                    stats["reminders_sent"] += 1
                    logger.info(f"Reminder sent to {reservation.email} for milestone {milestone.title}")
                else:
                    stats["errors"] += 1
                    
            except Exception as e:
                logger.error(f"Error sending reminder to {reservation.email}: {e}", exc_info=True)
                stats["errors"] += 1
    
    # コミット
    await db.commit()
    return stats

