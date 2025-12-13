
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text
from src.db.base import get_db, engine
from src.core.config import settings

# Read SQL
with open("backend/migration_add_public_cols.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

async def apply_migration():
    print(f"Applying migration to {settings.DATABASE_URL}")
    async with engine.begin() as conn:
        for statement in sql_script.split(";"):
            if statement.strip():
                print(f"Executing: {statement.strip()}")
                await conn.execute(text(statement))
    print("Migration complete.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(apply_migration())
