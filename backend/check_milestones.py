"""データベースのマイルストーン情報を確認するスクリプト."""
import asyncio
from sqlalchemy import select
from src.db import get_db_session
from src.db.models import Milestone, TheaterProject

async def check_milestones():
    """マイルストーンのis_public状態を確認."""
    async with get_db_session() as db:
        # 全マイルストーンを取得
        stmt = select(Milestone).join(TheaterProject, Milestone.project_id == TheaterProject.id)
        result = await db.execute(stmt)
        milestones = result.scalars().all()
        
        print(f"\n=== マイルストーン一覧 (合計: {len(milestones)}件) ===\n")
        for m in milestones:
            print(f"ID: {m.id}")
            print(f"Title: {m.title}")
            print(f"Project ID: {m.project_id}")
            print(f"is_public: {m.is_public}")
            print(f"Start Date: {m.start_date}")
            print(f"Reservation Capacity: {m.reservation_capacity}")
            print("-" * 50)
        
        # is_public=Trueのマイルストーンのみ
        public_milestones = [m for m in milestones if m.is_public]
        print(f"\n=== 公開マイルストーン (is_public=True): {len(public_milestones)}件 ===\n")
        for m in public_milestones:
            print(f"ID: {m.id} - {m.title}")

if __name__ == "__main__":
    asyncio.run(check_milestones())
