import asyncio
import os
import sys
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select

# Add current directory to path so we can import app modules
# Assumes script is run from project root or backend dir
sys.path.append(os.path.join(os.getcwd(), "backend")) 

from src.db import get_db, async_session_maker
from src.db.models import TheaterProject, Milestone
from src.schemas.project import MilestoneCreate

async def test_create_milestone():
    # Helper to get session since get_db is a generator
    async with async_session_maker() as db:
        # 1. Get a project
        result = await db.execute(select(TheaterProject))
        project = result.scalars().first()
        
        if not project:
            print("No projects found to test with.")
            # Create a dummy project if needed, or just exit
            return

        print(f"Testing with Project: {project.id} ({project.name})")

        # 2. Prepare Milestone Data
        milestone_data = MilestoneCreate(
            title="Test Milestone script",
            start_date=datetime.utcnow(),
            description="Created by debug script",
            color="#FF0000",
            location="Debug Location 123"
        )
        
        print(f"Milestone Data: {milestone_data}")

        # 3. Simulate Logic
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
            print(f"Saved Location: {new_milestone.location}")
            
            if new_milestone.location == "Debug Location 123":
                print("SUCCESS: Location saved correctly.")
            else:
                print("FAILURE: Location NOT saved correctly.")
                
            # Clean up
            await db.delete(new_milestone)
            await db.commit()
            print("Cleaned up test milestone.")
            
        except Exception as e:
            print(f"Failed to create milestone: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    # Ensure backend directory is in path if running from root
    if os.path.exists("backend"):
        sys.path.append("backend")
    
    asyncio.run(test_create_milestone())
