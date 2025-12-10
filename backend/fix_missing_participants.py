import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import User, TheaterProject, ProjectMember, Rehearsal, RehearsalSchedule, RehearsalParticipant
from src.config import settings

DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def fix_participants():
    async with AsyncSessionLocal() as db:
        print("--- Fixing Missing Participants ---")
        
        # 1. Find the main user
        stmt = select(User).where(User.discord_username != "ScheduleTester")
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        # Assuming the first non-tester user is the one
        target_user = None
        for u in users:
            # You might want to pick a specific one if multiple exist
            target_user = u
            break
            
        if not target_user:
            print("No target user found.")
            return

        print(f"Target User: {target_user.discord_username} ({target_user.id})")

        # 2. Find all projects the user is a member of
        stmt = (
            select(TheaterProject)
            .join(ProjectMember)
            .where(ProjectMember.user_id == target_user.id)
        )
        result = await db.execute(stmt)
        projects = result.scalars().all()
        
        print(f"Found {len(projects)} projects.")

        # 3. For each project, find rehearsals
        count = 0
        for project in projects:
            print(f"Checking Project: {project.name}")
            stmt = (
                select(Rehearsal)
                .join(RehearsalSchedule)
                .where(RehearsalSchedule.project_id == project.id)
            )
            result = await db.execute(stmt)
            rehearsals = result.scalars().all()
            
            for r in rehearsals:
                # Check if already participant
                stmt_check = select(RehearsalParticipant).where(
                    RehearsalParticipant.rehearsal_id == r.id,
                    RehearsalParticipant.user_id == target_user.id
                )
                res_check = await db.execute(stmt_check)
                existing = res_check.scalar_one_or_none()
                
                if not existing:
                    print(f" -> Adding participant to Rehearsal {r.date} ({r.id})")
                    new_part = RehearsalParticipant(
                        rehearsal_id=r.id,
                        user_id=target_user.id
                    )
                    db.add(new_part)
                    count += 1
        
        if count > 0:
            await db.commit()
            print(f"Successfully added {count} participation entries.")
        else:
            print("No missing participation entries found.")

if __name__ == "__main__":
    try:
        asyncio.run(fix_participants())
    except Exception:
        import traceback
        traceback.print_exc()
