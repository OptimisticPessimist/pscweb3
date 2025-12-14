import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

# Mocking the app structure
from src.db.models import Base, User, TheaterProject, RehearsalSchedule, Rehearsal, RehearsalParticipant, ProjectMember
from src.schemas.rehearsal import RehearsalUpdate, RehearsalParticipantUpdate

# Setup DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def reproduce():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 1. Create User A (Owner)
        user_a = User(id=uuid.uuid4(), discord_id="123", discord_username="UserA")
        db.add(user_a)
        
        # 2. Create Project
        project = TheaterProject(id=uuid.uuid4(), name="Test Project", created_by=user_a.id)
        db.add(project)
        
        member_a = ProjectMember(project_id=project.id, user_id=user_a.id, role="owner")
        db.add(member_a)
        
        await db.commit()

        # 3. Create Schedule
        schedule = RehearsalSchedule(id=uuid.uuid4(), project_id=project.id, script_id=uuid.uuid4())
        db.add(schedule)
        await db.commit()
        
        # 4. Create Rehearsal
        rehearsal = Rehearsal(
            id=uuid.uuid4(), 
            schedule_id=schedule.id, 
            date=datetime.now(timezone.utc),
            duration_minutes=60
        )
        db.add(rehearsal)
        await db.commit()
        
        print("Initial Rehearsal Created")

        # 5. Create User B (New Member)
        user_b = User(id=uuid.uuid4(), discord_id="456", discord_username="UserB")
        db.add(user_b)
        
        member_b = ProjectMember(project_id=project.id, user_id=user_b.id, role="viewer")
        db.add(member_b)
        await db.commit()
        
        print(f"User B Created: {user_b.id}")

        # 6. Simulate Update Rehearsal (Add User B)
        rehearsal_id = rehearsal.id
        
        # Emulate the update logic from api/rehearsals.py
        
        # Fetch Rehearsal
        result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
        r = result.scalar_one()
        
        # Update Participants
        await db.execute(delete(RehearsalParticipant).where(RehearsalParticipant.rehearsal_id == r.id))
        
        # Add User B as participant
        new_p = RehearsalParticipant(
            rehearsal_id=r.id,
            user_id=user_b.id,
            staff_role="New Guy"
        )
        db.add(new_p)
        await db.commit()
        
        print("Update Committed. Re-fetching...")

        # 7. Re-fetch
        result = await db.execute(
            select(Rehearsal)
            .where(Rehearsal.id == rehearsal_id)
            .options(
                selectinload(Rehearsal.participants).options(selectinload(RehearsalParticipant.user))
            )
        )
        r_refetched = result.scalar_one()
        
        print(f"Participants count: {len(r_refetched.participants)}")
        
        # 8. Simulate Response Construction
        for p in r_refetched.participants:
            print(f"Propcessing Participant: {p.user_id}")
            try:
                # This is the line that might fail if p.user is None or not loaded
                username = p.user.discord_username
                print(f"Username: {username}")
            except Exception as e:
                print(f"FAIL: {e}")
                raise e

if __name__ == "__main__":
    asyncio.run(reproduce())
