
import asyncio
import uuid
from fastapi import BackgroundTasks
from sqlalchemy import select
from src.db.base import Base
from src.db.models import User
from src.db import get_db
from src.api.projects import create_project
from src.schemas.project import ProjectCreate
from src.services.discord import DiscordService

async def debug_create():
    async for session in get_db():
        print("Session created.")
        try:
            # 1. Get a user
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if not user:
                print("No user found in DB. Creating one.")
                user = User(discord_id="debug_user", discord_username="DebugUser")
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            print(f"Using user: {user.discord_username} ({user.id})")
            
            # 2. Prepare data
            project_data = ProjectCreate(name="Debug Project", description="Created by debug script")
            bg_tasks = BackgroundTasks()
            discord_service = DiscordService()
            
            # 3. Call function
            print("Calling create_project...")
            try:
                project = await create_project(
                    project_data=project_data,
                    background_tasks=bg_tasks,
                    current_user=user,
                    db=session,
                    discord_service=discord_service
                )
                print(f"SUCCESS! Project created: {project.name} ({project.id})")
                print(f"Audit log should be created.")
            except Exception as e:
                print(f"FAILURE! create_project raised exception: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"Setup error: {e}")
        finally:
            # No rollback needed if we use session logic correctly, but explicit close is good
            pass
        break # Only one session needed

if __name__ == "__main__":
    asyncio.run(debug_create())
