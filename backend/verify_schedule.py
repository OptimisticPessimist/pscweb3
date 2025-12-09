import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, User, TheaterProject, ProjectMember, Milestone, Rehearsal, RehearsalSchedule, RehearsalParticipant, Scene
from src.config import settings

# Override database URL for testing if needed, or use dev DB
DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def verify_schedule():
    async with AsyncSessionLocal() as db:
        print("--- Verifying Schedule API Logic ---")
        
        # 1. Create Test User
        # Check if exists or create
        stmt = select(User).where(User.discord_username == "ScheduleTester")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(discord_id="999999", discord_username="ScheduleTester")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        print(f"User ID: {user.id}")

        # 2. Create Project A
        project_a = TheaterProject(name="Project A - Schedule Test")
        db.add(project_a)
        await db.commit()
        await db.refresh(project_a)
        
        # Add member
        member_a = ProjectMember(project_id=project_a.id, user_id=user.id, role="owner")
        db.add(member_a)
        
        # 3. Create Project B
        project_b = TheaterProject(name="Project B - Schedule Test")
        db.add(project_b)
        await db.commit()
        await db.refresh(project_b)
        
        # Add member
        member_b = ProjectMember(project_id=project_b.id, user_id=user.id, role="owner")
        db.add(member_b)
        await db.commit()

        from src.db.models import Script

        # Create Script for Project A
        script = Script(
            project_id=project_a.id,
            uploaded_by=user.id,
            title="Test Script",
            content="INT. TEST - DAY\n\nTesting."
        )
        db.add(script)
        await db.flush()

        # 4. Create Rehearsal in Project A (User participates)
        schedule_a = RehearsalSchedule(project_id=project_a.id, script_id=script.id)
        db.add(schedule_a)
        await db.commit()
        await db.refresh(schedule_a)
        
        rehearsal_a = Rehearsal(
            schedule_id=schedule_a.id,
            date=datetime.utcnow() + timedelta(days=1),
            duration_minutes=60,
            location="Studio A"
        )
        db.add(rehearsal_a)
        await db.commit()
        await db.refresh(rehearsal_a)
        
        part_a = RehearsalParticipant(rehearsal_id=rehearsal_a.id, user_id=user.id)
        db.add(part_a)
        
        # 5. Create Milestone in Project B
        milestone_b = Milestone(
            project_id=project_b.id,
            title="Performance B",
            start_date=datetime.utcnow() + timedelta(days=2),
            color="#FF0000"
        )
        db.add(milestone_b)
        
        await db.commit()
        
        print("Data created. Fetching schedule via logic...")
        
        # 6. Simulate API Query
        from src.api.users import get_my_schedule
        # We cannot call endpoint directly easily without mocking auth dependency, 
        # so let's check logic with direct queries similar to endpoint.
        
        from sqlalchemy.orm import selectinload
        from sqlalchemy import or_

        # Rehearsals query
        rehearsal_stmt = (
            select(Rehearsal)
            .join(Rehearsal.schedule)
            .join(TheaterProject, RehearsalSchedule.project_id == TheaterProject.id)
            .outerjoin(RehearsalParticipant, Rehearsal.id == RehearsalParticipant.rehearsal_id)
            # .outerjoin(RehearsalCast) # Check casts too if needed
            .options(
                selectinload(Rehearsal.schedule).selectinload(RehearsalSchedule.project),
                selectinload(Rehearsal.scene)
            )
            .where(
                or_(
                    RehearsalParticipant.user_id == user.id,
                    # RehearsalCast...
                )
            )
            .distinct()
        )
        r_result = await db.execute(rehearsal_stmt)
        rehearsals = r_result.scalars().all()
        print(f"Found {len(rehearsals)} rehearsals. (Expected 1)")
        for r in rehearsals:
            print(f" - Rehearsal: {r.date} {r.schedule.project.name}")

        # Milestones query
        milestone_stmt = (
            select(Milestone)
            .join(TheaterProject, Milestone.project_id == TheaterProject.id)
            .join(ProjectMember, TheaterProject.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user.id)
            .options(selectinload(Milestone.project))
        )
        m_result = await db.execute(milestone_stmt)
        milestones = m_result.scalars().all()
        print(f"Found {len(milestones)} milestones. (Expected at least 1)")
        for m in milestones:
            print(f" - Milestone: {m.start_date} {m.title} ({m.project.name})")

        # Combine
        combined = []
        for r in rehearsals:
            combined.append({"date": r.date, "type": "rehearsal"})
        for m in milestones:
            combined.append({"date": m.start_date, "type": "milestone"})
        
        combined.sort(key=lambda x: x["date"])
        print("Combined Sorted Schedule:")
        for item in combined:
            print(f"[{item['type']}] {item['date']}")
            
        print("Verification Complete.")
        
        # Cleanup (Optional)
        # await db.delete(project_a)
        # await db.delete(project_b)
        # await db.delete(user)
        # await db.commit()

if __name__ == "__main__":
    try:
        asyncio.run(verify_schedule())
    except Exception as e:
        import traceback
        with open("verification_error.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        sys.exit(1)
