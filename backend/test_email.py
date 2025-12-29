"""メール送信テストスクリプト."""
import os
import sys
from pathlib import Path

# backendディレクトリをカレントディレクトリとして設定
backend_dir = Path(__file__).parent
os.chdir(backend_dir)
print(f"Current directory: {os.getcwd()}")
print(f".env file exists: {(backend_dir / '.env').exists()}")

from dotenv import load_dotenv

# .envファイルを明示的に読み込み
env_path = backend_dir / '.env'
load_dotenv(env_path, verbose=True)

print(f"\n環境変数確認:")
print(f"SENDGRID_API_KEY: {'*' * 20 if os.getenv('SENDGRID_API_KEY') else 'None'}")
print(f"FROM_EMAIL: {os.getenv('FROM_EMAIL')}")

from src.services.email import email_service

# テスト実行
result = email_service.send_reservation_confirmation(
    to_email="new.folder.booth@gmail.com",  # 実際のメールアドレス
    name="テストユーザー",
    milestone_title="テスト公演",
    date_str="2025/12/30 19:00",
    count=2,
    project_name="テスト劇団",
    reservation_id="test-reservation-id-123",
    location="東京都渋谷区テスト会場",
    description="これはテスト用の説明文です。"
)

print(f"\nメール送信結果: {'✅ 成功' if result else '❌ 失敗'}")
