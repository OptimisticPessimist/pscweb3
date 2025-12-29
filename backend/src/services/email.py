import logging
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@example.com")
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def send_reservation_confirmation(
        self, 
        to_email: str, 
        name: str, 
        milestone_title: str, 
        date_str: str, 
        count: int, 
        project_name: str, 
        reservation_id: str,
        location: str | None = None,  # 🆕 場所を追加
        description: str | None = None  # 🆕 説明を追加
    ) -> bool:
        """予約確認メールを送信する."""
        if not self.client:
            logger.warning("SendGrid API Client is not initialized. Skip sending email.")
            return False

        subject = f"【予約完了】{project_name} - {milestone_title} チケット予約のお知らせ"
        
        # 場所と説明の追加
        location_info = f"■ 場所: {location}\n" if location else ""
        description_info = f"\n{description}\n" if description else ""
        
        content = f"""
{name} 様

この度はご予約いただきありがとうございます。
以下の内容でチケットの予約を承りました。

━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 予約ID: {reservation_id}
■ 劇団名: {project_name}
■ 公演名: {milestone_title}
■ 日時: {date_str}
{location_info}■ 枚数: {count} 枚
━━━━━━━━━━━━━━━━━━━━━━━━━━
{description_info}
キャンセル等の際は、上記「予約ID」が必要となりますので大切に保管してください。

当日は受付にてお名前をお伝えください。
ご来場を心よりお待ちしております。

※このメールは送信専用アドレスから送信されています。
"""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )

        try:
            response = self.client.send(message)
            logger.info(f"Email sent to {to_email}. Status Code: {response.status_code}")
            return str(response.status_code).startswith("2")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_event_reminder(
        self, to_email: str, name: str, milestone_title: str, date_str: str, count: int, project_name: str, location: str | None = None
    ) -> bool:
        """公演当日のリマインダーメールを送信する."""
        if not self.client:
            logger.warning("SendGrid API Client is not initialized. Skip sending email.")
            return False

        subject = f"【本日開催】{project_name} - {milestone_title} のご案内"
        
        location_info = f"■ 会場: {location}\n" if location else ""
        
        content = f"""
{name} 様

本日は{milestone_title}の開催日です。
ご来場をお待ちしております。

━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 劇団名: {project_name}
■ 公演名: {milestone_title}
■ 日時: {date_str}
{location_info}■ 予約枚数: {count} 枚
━━━━━━━━━━━━━━━━━━━━━━━━━━
{description_info}
受付にてお名前をお伝えください。
皆様のご来場を心よりお待ちしております。

※このメールは送信専用アドレスから送信されています。
"""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )

        try:
            response = self.client.send(message)
            logger.info(f"Event reminder email sent to {to_email}. Status Code: {response.status_code}")
            return str(response.status_code).startswith("2")
        except Exception as e:
            logger.error(f"Failed to send event reminder email to {to_email}: {e}")
            return False

email_service = EmailService()
