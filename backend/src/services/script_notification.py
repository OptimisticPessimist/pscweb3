"""スクリプト通知サービス."""

from uuid import UUID

from src.db.models import Script, TheaterProject, User
from src.services.discord_service import DiscordService


async def send_script_notification(
    script: Script,
    project: TheaterProject,
    current_user: User,
    is_update: bool,
    discord_service: DiscordService,
) -> None:
    """スクリプトアップロード/更新のDiscord通知を送信.
    
    Args:
        script: スクリプト
        project: プロジェクト
        current_user: アップロードユーザー
        is_update: 更新フラグ
        discord_service: Discordサービス
    """
    action_text = "更新" if is_update else "新規アップロード"
    revision_text = f" (Rev.{script.revision})" if script.revision > 1 else ""
    message = (
        f"📝 **脚本が{action_text}されました{revision_text}**\n"
        f"プロジェクト: {project.name}\n"
        f"タイトル: {script.title}\n"
        f"ユーザー: {current_user.discord_username}"
    )
    
    # PDF生成（通知添付用）
    pdf_file = None
    try:
        from src.services.pdf_generator import generate_script_pdf
        
        pdf_bytes = generate_script_pdf(script.content)
        pdf_file = {"filename": f"{script.title}.pdf", "content": pdf_bytes}
    except Exception as e:
        # PDF生成失敗しても通知は送る
        message += f"\n\n⚠️ PDF生成に失敗しました: {e}"
    
    # Discord通知送信
    await discord_service.send_notification(
        content=message, webhook_url=project.discord_webhook_url, file=pdf_file
    )
