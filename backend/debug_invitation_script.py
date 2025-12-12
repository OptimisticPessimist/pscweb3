import asyncio
import uuid
# Print debug info
import sys
import os
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")
sys.path.append(os.getcwd()) # Ensure CWD is in path


from sqlalchemy import select
from src.db.session import async_session_maker
from src.db.models import User, TheaterProject, ProjectMember
from src.api.invitations import create_invitation
from src.schemas.invitation import InvitationCreate

async def main():
    async with async_session_maker() as db:
        print("Finding a project and an owner...")
        
        # Find a project member who is an owner
        query = select(ProjectMember).where(ProjectMember.role == "owner").limit(1)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            print("No project owner found. Cannot test.")
            return

        user = await db.get(User, member.user_id)
        project = await db.get(TheaterProject, member.project_id)
        
        print(f"Testing with User: {user.discord_username} ({user.id})")
        print(f"Project: {project.name} ({project.id})")
        print(f"Project ID Type: {type(project.id)}")

        invitation_in = InvitationCreate(
            expires_in_hours=24,
            max_uses=None
        )

        try:
            print("Calling create_invitation...")
            # Call the function directly
            response = await create_invitation(
                project_id=project.id,
                invitation_in=invitation_in,
                current_user=user,
                db=db
            )
            print("Success!")
            print(f"Token: {response.token}")
        except Exception as e:
            print(f"Error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
