"""データベースマイグレーション: タイムゾーン対応."""

import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# .envファイルを手動で読み込み
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

async def run_migration():
    """マイグレーションを実行."""
    # DATABASE_URLを取得
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        return
    
    # asyncpg用のURLに変換
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=True)
    
    # マイグレーションSQLを読み込み
    sql_path = Path(__file__).parent / "migrations" / "timezone_migration.sql"
    with open(sql_path, "r", encoding="utf-8") as f:
        migration_sql = f.read()
    
    # セミコロンで分割して個別に実行
    statements = [s.strip() for s in migration_sql.split(";") if s.strip()]
    
    async with engine.begin() as conn:
        for i, statement in enumerate(statements, 1):
            try:
                print(f"\n[{i}/{len(statements)}] Executing statement...")
                print(f"{statement[:100]}...")
                await conn.execute(text(statement))
                print(f"✓ Success")
            except Exception as e:
                print(f"✗ Error: {e}")
                # 継続するかどうか
                if "does not exist" in str(e):
                    print("  (Skipping - already migrated)")
                    continue
                else:
                    raise
    
    print("\n✅ Migration completed successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
