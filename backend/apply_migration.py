
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

import asyncio
from sqlalchemy import text
from src.db import get_db, engine
from src.config import settings

# Read SQL
basedir = os.path.dirname(__file__)
migration_files = [
    "migration_add_public_cols.sql",
    "migration_add_project_is_public.sql"
]

async def apply_migration():
    print(f"Applying migration to {settings.database_url}")
    async with engine.begin() as conn:
        for filename in migration_files:
            sql_path = os.path.join(basedir, filename)
            if not os.path.exists(sql_path):
                print(f"Skipping {filename}: Not found")
                continue
                
            print(f"Applying {filename}...")
            with open(sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
                
            for statement in sql_script.split(";"):
                if statement.strip():
                    print(f"Executing: {statement.strip()}")
                    await conn.execute(text(statement))
    print("All migrations complete.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(apply_migration())
