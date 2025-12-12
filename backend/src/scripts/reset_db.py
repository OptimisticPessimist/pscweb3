import asyncio
import sys
import os

# パスを追加して src モジュールが見つかるようにする
# backend ディレクトリのルートを sys.path に追加
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.join(current_dir, "../..")
sys.path.append(backend_root)

from src.db import engine
from src.db.base import Base
# モデルを全てインポートして Base.metadata に登録させる
from src.db.models import (
    User, ProjectMember, TheaterProject, Script, Scene, Character, Line,
    SceneChart, SceneCharacterMapping, CharacterCasting, NotificationSettings,
    RehearsalSchedule, Rehearsal, RehearsalScene, RehearsalParticipant, RehearsalCast,
    ProjectInvitation, AuditLog, Milestone, AttendanceEvent, AttendanceTarget
)

async def reset_database():
    print(f"Connecting to database via engine: {engine.url}")
    print("Resetting database...")
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(reset_database())
