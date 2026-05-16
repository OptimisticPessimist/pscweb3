"""定時実行タスク：出欠確認のリマインダー."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from src.db import async_session_maker
from src.db.models import AttendanceEvent, AttendanceTarget, TheaterProject
from src.services.discord import get_discord_service

logger = logging.getLogger(__name__)


async def check_deadlines() -> dict[str, int]:
    """期限切れおよびリマインド設定時間に応じた開始前リマインドをチェックし、送信する.

    Returns:
        dict[str, int]: 処理結果の統計
    """
    stats = {
        "checked_events": 0,
        "schedule_reminders_sent": 0,
        "deadline_reminders_sent": 0,
        "past_events_skipped": 0,
        "errors": 0,
    }

    async with async_session_maker() as db:
        now = datetime.now(UTC)

        # 全ての未完了イベントを取得（プロジェクトのリマインド設定を考慮するため一旦広く取る）
        stmt = (
            select(AttendanceEvent)
            .where(
                AttendanceEvent.completed == False,  # noqa: E712
                or_(
                    AttendanceEvent.reminder_1_sent_at.is_(None),
                    AttendanceEvent.reminder_2_sent_at.is_(None),
                    AttendanceEvent.reminder_3_sent_at.is_(None),
                ),
            )
            .options(
                selectinload(AttendanceEvent.targets).selectinload(AttendanceTarget.user),
                selectinload(AttendanceEvent.project),
            )
        )

        result = await db.execute(stmt)
        events = result.scalars().all()
        stats["checked_events"] = len(events)

        for event in events:
            try:
                if not event.project:
                    logger.warning(f"Project not found for event {event.id}")
                    stats["errors"] += 1
                    continue

                project = event.project
                reminded_this_run = False

                # 未回答(pending)のターゲットを抽出
                pending_targets = [t for t in event.targets if t.status == "pending"]
                # 不参加(ng)以外のターゲットを抽出
                not_absent_targets = [t for t in event.targets if t.status != "ng"]

                if not pending_targets:
                    # 未回答者がいない場合は1回目・2回目は送信済みとしてマーク
                    if event.reminder_1_sent_at is None:
                        event.reminder_1_sent_at = now
                    if event.reminder_2_sent_at is None:
                        event.reminder_2_sent_at = now

                if not not_absent_targets:
                    # 不参加以外がいない場合は3回目も送信済みとしてマーク
                    if event.reminder_3_sent_at is None:
                        event.reminder_3_sent_at = now

                # 稽古日未定ならスキップ
                if event.schedule_date is None:
                    continue

                # 稽古日が過去ならリマインダー不要 → 送信済みマークして次へ
                if now >= event.schedule_date:
                    if event.reminder_1_sent_at is None:
                        event.reminder_1_sent_at = now
                    if event.reminder_2_sent_at is None:
                        event.reminder_2_sent_at = now
                    if event.reminder_3_sent_at is None:
                        event.reminder_3_sent_at = now
                    stats["past_events_skipped"] += 1
                    logger.info(
                        f"Skipped past event {event.id} "
                        f"(schedule_date={event.schedule_date})"
                    )
                    continue

                # 1. 1回目のリマインダー判定
                if event.reminder_1_sent_at is None:
                    trigger_time = event.schedule_date - timedelta(
                        hours=project.attendance_reminder_1_hours
                    )
                    if now >= trigger_time:
                        sent = await _send_reminder(
                            event, pending_targets, project, reminder_type="1"
                        )
                        event.reminder_1_sent_at = now
                        if sent:
                            stats["schedule_reminders_sent"] += 1
                            reminded_this_run = True

                # 2. 2回目のリマインダー判定
                if event.reminder_2_sent_at is None and not reminded_this_run:
                    trigger_time = event.schedule_date - timedelta(
                        hours=project.attendance_reminder_2_hours
                    )
                    if now >= trigger_time and pending_targets:
                        sent = await _send_reminder(
                            event, pending_targets, project, reminder_type="2"
                        )
                        event.reminder_2_sent_at = now
                        if sent:
                            stats["deadline_reminders_sent"] += 1
                            reminded_this_run = True

                # 3. 3回目のリマインダー判定（不参加以外全員）
                if event.reminder_3_sent_at is None and not reminded_this_run:
                    trigger_time = event.schedule_date - timedelta(
                        hours=project.attendance_reminder_3_hours
                    )
                    if now >= trigger_time and not_absent_targets:
                        sent = await _send_reminder(
                            event, not_absent_targets, project, reminder_type="3"
                        )
                        event.reminder_3_sent_at = now
                        if sent:
                            stats["schedule_reminders_sent"] += 1
                            reminded_this_run = True

            except Exception as e:
                logger.error(f"Error processing event {event.id}: {e}", exc_info=True)
                stats["errors"] += 1

        await db.commit()

    return stats


async def _send_reminder(
    event: AttendanceEvent,
    targets: list[AttendanceTarget],
    project: TheaterProject,
    reminder_type: str = "1",
) -> bool:
    """Discordリマインダー送信.

    Args:
        reminder_type: "1" (1回目), "2" (2回目), or "3" (3回目)

    Returns:
        bool: 送信成功の場合True
    """
    if not project.discord_channel_id:
        return False

    mentions = [f"<@{t.user.discord_id}>" for t in targets if t.user and t.user.discord_id]

    if not mentions:
        return False

    deadline_ts = int(event.deadline.replace(tzinfo=UTC).timestamp())
    deadline_str = f"<t:{deadline_ts}:f>"

    schedule_str = "未定"
    if event.schedule_date:
        schedule_ts = int(event.schedule_date.replace(tzinfo=UTC).timestamp())
        schedule_str = f"<t:{schedule_ts}:f>"

    # リマインダーの種類に応じてメッセージのヘッダーを変更
    if reminder_type == "1":
        hour_text = project.attendance_reminder_1_hours
        header = f"**【自動リマインダー】間もなく稽古({hour_text}時間前)ですが、出欠が未回答です**"
        mention_label = "未回答の方"
        footer = "回答をお願いします。"
    elif reminder_type == "2":
        hour_text = project.attendance_reminder_2_hours
        header = f"**【自動リマインダー】間もなく稽古({hour_text}時間前)ですが、出欠が未回答です**"
        mention_label = "未回答の方"
        footer = "回答をお願いします。"
    else:
        hour_text = project.attendance_reminder_3_hours
        header = f"**【自動リマインダー】間もなく稽古({hour_text}時間前)です。出席予定の方は忘れずにご参加ください**"
        mention_label = "対象の方"
        footer = "※未回答の方は至急出欠を入力してください。"

    message_content = (
        f"{header}\n"
        f"イベント: **{event.title}**\n"
        f"日時: {schedule_str}\n"
        f"期限: {deadline_str}\n"
        f"{mention_label}: {' '.join(mentions)}\n\n"
        f"{footer}"
    )

    discord_service = get_discord_service()
    await discord_service.send_channel_message(
        channel_id=project.discord_channel_id, content=message_content
    )
    logger.info(
        f"Sent {reminder_type} reminder to {project.discord_channel_id} for event {event.id}"
    )
    return True
