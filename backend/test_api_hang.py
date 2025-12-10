import asyncio
import httpx
import os
import sys

# Try to get project ID from the DB first so we have a valid one
sys.path.append(os.path.join(os.getcwd(), "backend"))
from src.db.database import async_session_maker
from src.db.models import TheaterProject, User, ProjectMember
from sqlalchemy import select

async def test_live_api():
    async with async_session_maker() as db:
        # Get a project and a user who is an owner
        stmt = (
            select(TheaterProject, User)
            .join(ProjectMember, ProjectMember.project_id == TheaterProject.id)
            .join(User, User.id == ProjectMember.user_id)
            .where(ProjectMember.role == "owner")
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.first()
        
        if not row:
            print("No suitable project/user found for test.")
            return
            
        project, user = row
        print(f"Target Project: {project.id}")
        print(f"Target User: {user.discord_username}")

    # Now define the payload exactly as the frontend would send it
    # Frontend sends ISO string: "2025-12-09T10:00:00.000Z"
    payload = {
        "title": "Live API Test Milestone",
        "start_date": "2025-12-09T10:00:00.000Z",
        "location": "Live Test Location",
        "color": "#00FF00",
        "description": "Created via httpx"
    }

    print("Sending POST request to /api/projects/{id}/milestones...")
    
    # We need to simulate authentication. 
    # Since we can't easily generate a valid JWT without the secret (which is in env/config),
    # we might need to rely on the backend test I wrote earlier?
    # actually wait, I can modify `test_create_milestone_v2.py` to use the API *handler* directly? 
    # Or I can just check if the server is ALIVE first.
    
    try:
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
            # 1. Check health/root
            print("Checking root endpoint...")
            resp = await client.get("/api/users/me") # This will fail 401 but confirms server talks
            print(f"Root check status: {resp.status_code}") # Should be 401
            
            # If server is hanging, this will timeout
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_api())
