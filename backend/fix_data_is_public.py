import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, update
from src.db import get_db, engine
from src.db.models import TheaterProject, Script
from src.config import settings

async def fix_project_is_public():
    print("Starting data fix for TheaterProject.is_public...")
    report = []
    
    async for db in get_db():
        # Get all projects
        result = await db.execute(select(TheaterProject))
        projects = result.scalars().all()
        
        updated_count = 0
        
        for project in projects:
            # Check if project has any public script
            script_res = await db.execute(
                select(Script).where(Script.project_id == project.id, Script.is_public == True)
            )
            public_script = script_res.scalar_one_or_none()
            
            should_be_public = public_script is not None
            
            status = {
                "id": str(project.id),
                "name": project.name,
                "current_is_public": project.is_public,
                "should_be_public": should_be_public,
                "action": "none"
            }
            
            if project.is_public != should_be_public:
                print(f"Updating Project '{project.name}' (ID: {project.id}): is_public {project.is_public} -> {should_be_public}")
                project.is_public = should_be_public
                db.add(project)
                updated_count += 1
                status["action"] = "updated"
            
            report.append(status)
                
        if updated_count > 0:
            await db.commit()
            print(f"Successfully updated {updated_count} projects.")
        else:
            print("No projects needed update.")
            
        break # get_db is a generator, we only need one session
        
    return report

if __name__ == "__main__":
    asyncio.run(fix_project_is_public())
