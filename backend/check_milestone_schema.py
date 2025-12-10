import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Need to set up path to import config
sys.path.append(os.path.join(os.getcwd(), "backend"))
from src.config import settings


async def check_columns():
    # Force use of real DB if needed, but assuming settings loaded correctly from .env in backend dir
    engine = create_async_engine(settings.database_url)

    async with engine.connect() as conn:
        print(f"Checking milestones table in: {settings.database_url}")

        # Postgres query to get columns
        query = text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'milestones';")
        result = await conn.execute(query)

        columns = result.fetchall()
        print("Columns in 'milestones' table:")
        found_location = False
        for col_name, data_type in columns:
            print(f"- {col_name}: {data_type}")
            if col_name == 'location':
                found_location = True

        if found_location:
            print("\nSUCCESS: 'location' column FOUND.")
        else:
            print("\nFAILURE: 'location' column NOT FOUND.")

if __name__ == "__main__":
    if os.path.exists("backend"):
        sys.path.append("backend")
    asyncio.run(check_columns())
