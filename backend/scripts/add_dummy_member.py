import asyncio
import os
import sys

# パスを通す
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select

from src.db import async_session_maker
from src.db.models import ProjectMember, TheaterProject, User


async def create_dummy_user(project_name_keyword: str = None):
    async with async_session_maker() as db:
        # 1. ダミーユーザー作成
        dummy_discord_id = "dummy_12345"
        dummy_username = "DramaActor_A"

        result = await db.execute(select(User).where(User.discord_id == dummy_discord_id))
        user = result.scalar_one_or_none()

        if not user:
            print(f"Creating dummy user: {dummy_username}")
            user = User(
                discord_id=dummy_discord_id,
                discord_username=dummy_username
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            print(f"Dummy user already exists: {user.discord_username}")

        # 2. プロジェクト取得
        # 最新のプロジェクトまたはキーワードで検索
        if project_name_keyword:
            stmt = select(TheaterProject).where(TheaterProject.name.contains(project_name_keyword))
        else:
            stmt = select(TheaterProject).order_by(TheaterProject.created_at.desc())

        result = await db.execute(stmt)
        project = result.scalars().first()

        if not project:
            print("No projects found.")
            return

        print(f"Target Project: {project.name} ({project.id})")

        # 3. メンバー追加
        result = await db.execute(select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id
        ))
        member = result.scalar_one_or_none()

        if not member:
            print("Adding user to project...")
            member = ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role="editor" # 編集権限あり
            )
            db.add(member)
            await db.commit()
            print("Done.")
        else:
            print("User is already a member.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(create_dummy_user(sys.argv[1]))
    else:
        asyncio.run(create_dummy_user())
