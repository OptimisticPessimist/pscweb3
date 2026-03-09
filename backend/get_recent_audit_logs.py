import asyncio
import os
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

async def main():
    if not DATABASE_URL:
        print("No DATABASE_URL found.")
        return

    # Fix for pgbouncer pool mode
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0
        }
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    data = {"logs": [], "users": []}
    
    async with async_session() as session:
        try:
            result = await session.execute(text(
                "SELECT id, event, user_id, project_id, details, ip_address, created_at "
                "FROM audit_logs "
                "WHERE created_at > NOW() - INTERVAL '5 days' "
                "ORDER BY created_at DESC LIMIT 50"
            ))
            for row in result:
                data["logs"].append({
                    "id": str(row.id),
                    "event": row.event,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "project_id": str(row.project_id) if row.project_id else None,
                    "details": row.details,
                    "ip_address": row.ip_address,
                    "created_at": row.created_at
                })
        except Exception as e:
            data["logs_error"] = str(e)
        
        try:
            result_users = await session.execute(text(
                "SELECT id, discord_username, screen_name, created_at "
                "FROM users "
                "WHERE created_at > NOW() - INTERVAL '5 days' "
                "ORDER BY created_at DESC LIMIT 20"
            ))
            for row in result:
                data["users"].append({
                    "id": str(row.id),
                    "discord_username": row.discord_username,
                    "screen_name": row.screen_name,
                    "created_at": row.created_at
                })
        except Exception as e:
            data["users_error"] = str(e)

    with open("audit_logs_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
    print("Done. Wrote to audit_logs_output.json")

if __name__ == "__main__":
    asyncio.run(main())
