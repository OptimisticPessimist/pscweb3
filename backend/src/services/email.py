import logging
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@example.com")
        self.from_name = os.getenv("FROM_NAME", "PSC Web")
        self.reply_to_email = os.getenv("REPLY_TO_EMAIL", self.from_email)
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
        
        # テキスト版
        text_content = f"""
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
        
        # HTML版
        location_html = f"<tr><td style='padding:8px 0;'><strong>■ 場所:</strong> {location}</td></tr>" if location else ""
        description_html = f"<div style='margin:15px 0; padding:15px; background:#f9f9f9; border-left:3px solid #4CAF50;'>{description}</div>" if description else ""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🎭 チケット予約完了</h1>
    </div>
    
    <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">{name} 様</p>
        
        <p>この度はご予約いただきありがとうございます。<br>
        以下の内容でチケットの予約を承りました。</p>
        
        <table style="width: 100%; margin: 20px 0; background: #f5f5f5; border-radius: 8px; padding: 20px;">
            <tr><td style="padding:8px 0;"><strong>■ 予約ID:</strong> {reservation_id}</td></tr>
            <tr><td style="padding:8px 0;"><strong>■ 劇団名:</strong> {project_name}</td></tr>
            <tr><td style="padding:8px 0;"><strong>■ 公演名:</strong> {milestone_title}</td></tr>
            <tr><td style="padding:8px 0;"><strong>■ 日時:</strong> {date_str}</td></tr>
            {location_html}
            <tr><td style="padding:8px 0;"><strong>■ 枚数:</strong> {count} 枚</td></tr>
        </table>
        
        {description_html}
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <p style="margin: 0;">⚠️ キャンセル等の際は、上記「予約ID」が必要となりますので大切に保管してください。</p>
        </div>
        
        <p>当日は受付にてお名前をお伝えください。<br>
        ご来場を心よりお待ちしております。</p>
        
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="font-size: 12px; color: #999; text-align: center;">※このメールは送信専用アドレスから送信されています。</p>
    </div>
</body>
</html>
"""
        
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=subject,
            plain_text_content=text_content,
            html_content=html_content
        )
        message.reply_to = self.reply_to_email

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
        
        # テキスト版
        text_content = f"""
{name} 様

本日は{milestone_title}の開催日です。
ご来場をお待ちしております。

━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 劇団名: {project_name}
■ 公演名: {milestone_title}
■ 日時: {date_str}
{location_info}■ 予約枚数: {count} 枚
━━━━━━━━━━━━━━━━━━━━━━━━━━

受付にてお名前をお伝えください。
皆様のご来場を心よりお待ちしております。

※このメールは送信専用アドレスから送信されています。
"""
        
        # HTML版
        location_html = f"<tr><td style='padding:8px 0;'><strong>■ 会場:</strong> {location}</td></tr>" if location else ""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🎉 本日開催のご案内</h1>
    </div>
    
    <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">{name} 様</p>
        
        <p style="font-size: 18px; color: #f5576c; font-weight: bold;">本日は{milestone_title}の開催日です。<br>
        ご来場をお待ちしております。</p>
        
        <table style="width: 100%; margin: 20px 0; background: #f5f5f5; border-radius: 8px; padding: 20px;">
            <tr><td style="padding:8px 0;"><strong>■ 劇団名:</strong> {project_name}</td></tr>
            <tr><td style="padding:8px 0;"><strong>■ 公演名:</strong> {milestone_title}</td></tr>
            <tr><td style="padding:8px 0;"><strong>■ 日時:</strong> {date_str}</td></tr>
            {location_html}
            <tr><td style="padding:8px 0;"><strong>■ 予約枚数:</strong> {count} 枚</td></tr>
        </table>
        
        <p>受付にてお名前をお伝えください。<br>
        皆様のご来場を心よりお待ちしております。</p>
        
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="font-size: 12px; color: #999; text-align: center;">※このメールは送信専用アドレスから送信されています。</p>
    </div>
</body>
</html>
"""
        
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=subject,
            plain_text_content=text_content,
            html_content=html_content
        )
        message.reply_to = self.reply_to_email

        try:
            response = self.client.send(message)
            logger.info(f"Event reminder email sent to {to_email}. Status Code: {response.status_code}")
            return str(response.status_code).startswith("2")
        except Exception as e:
            logger.error(f"Failed to send event reminder email to {to_email}: {e}")
            return False

email_service = EmailService()
