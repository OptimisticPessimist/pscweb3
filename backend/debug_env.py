"""環境変数デバッグスクリプト."""
import os
from pathlib import Path

backend_dir = Path(__file__).parent
env_file = backend_dir / '.env'

print(f"=== 環境変数デバッグ ===")
print(f"Current directory: {os.getcwd()}")
print(f".env path: {env_file}")
print(f".env exists: {env_file.exists()}")

if env_file.exists():
    print(f"\n.envファイルの内容を確認:")
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            # SENDGRID関連の行のみ表示（APIキーは一部マスク）
            if 'SENDGRID' in line or 'FROM_EMAIL' in line:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    if 'API_KEY' in key:
                        print(f"Line {i}: {key}={'*' * 20}... (長さ: {len(value.strip())})")
                    else:
                        print(f"Line {i}: {line.strip()}")
                else:
                    print(f"Line {i}: {line.strip()}")

print(f"\n=== python-dotenv でロード ===")
from dotenv import load_dotenv
loaded = load_dotenv(env_file, verbose=True, override=True)
print(f"load_dotenv result: {loaded}")

print(f"\n=== os.getenv()で確認 ===")
api_key = os.getenv('SENDGRID_API_KEY')
from_email = os.getenv('FROM_EMAIL')
print(f"SENDGRID_API_KEY: {'*' * 20 if api_key else 'None'} (長さ: {len(api_key) if api_key else 0})")
print(f"FROM_EMAIL: {from_email if from_email else 'None'}")
