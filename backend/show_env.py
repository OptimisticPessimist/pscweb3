"""環境変数内容確認スクリプト."""
from pathlib import Path

backend_dir = Path(__file__).parent
env_file = backend_dir / '.env'

print(f"=== .envファイルの全内容 ===\n")
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()
    print(content)

print(f"\n=== 行ごとの分析 ===")
with open(env_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        # 空行やコメントもすべて表示
        print(f"Line {i:3d}: {repr(line)}")
