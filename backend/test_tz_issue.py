import asyncio
import os
import sys
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import select

# Add current directory to path so we can import app modules
# Assumes script is run from project root or backend dir
sys.path.append(os.path.join(os.getcwd(), "backend")) 

from src.db import get_db, async_session_maker
from src.db.models import TheaterProject, Milestone
from src.schemas.project import MilestoneCreate

async def test_create_milestone_tz():
    async with async_session_maker() as db:
        # 1. Get a project
        result = await db.execute(select(TheaterProject))
        project = result.scalars().first()
        
        if not project:
            print("No projects found to test with.")
            return

        print(f"Testing with Project: {project.id} ({project.name})")

        # 2. Prepare Milestone Data with TIMEZONE AWARE datetime (like frontend sends)
        # 2025-12-09T10:00:00Z
        aware_date = datetime(2025, 12, 9, 10, 0, 0, tzinfo=timezone.utc)
        
        milestone_data = MilestoneCreate(
            title="Test Milestone TZ Check",
            start_date=aware_date,
            description="Created by debug script",
            color="#FF0000",
            location="Debug Location TZ"
        )
        
        print(f"Milestone Data: {milestone_data}")
        print(f"Start Date TZ Info: {milestone_data.start_date.tzinfo}")

        # 3. Simulate Logic from api/projects.py (using raw attributes)
        new_milestone = Milestone(
            project_id=project.id,
            title=milestone_data.title,
            start_date=milestone_data.start_date,
            end_date=milestone_data.end_date,
            description=milestone_data.description,
            location=milestone_data.location,
            color=milestone_data.color,
        )
        
        print("Adding milestone to DB...")
        db.add(new_milestone)
        try:
            await db.commit()
            await db.refresh(new_milestone)
            print(f"Successfully created milestone: {new_milestone.id}")
            
            # Clean up
            await db.delete(new_milestone)
            await db.commit()
            print("Cleaned up test milestone.")
            
        except Exception as e:
            print(f"Failed to create milestone: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    if os.path.exists("backend"):
        sys.path.append("backend")
    asyncio.run(test_create_milestone_tz())
