import pytest
import uuid
from sqlalchemy import select
from src.db.models import User, TheaterProject, ProjectMember, ProjectInvitation
from src.api.invitations import create_invitation
from src.schemas.invitation import InvitationCreate
from src.db import async_session_maker

@pytest.mark.asyncio
async def test_create_invitation_manual():
    async with async_session_maker() as db:
        # Find an owner
        query = select(ProjectMember).where(ProjectMember.role == "owner").limit(1)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            pytest.skip("No project owner found")

        user = await db.get(User, member.user_id)
        project = await db.get(TheaterProject, member.project_id)
        
        print(f"\nTesting with User: {user.discord_username} ({user.id})")
        print(f"Project: {project.name} ({project.id})")

        invitation_in = InvitationCreate(
            expires_in_hours=24,
            max_uses=None
        )

        response = await create_invitation(
            project_id=project.id,
            invitation_in=invitation_in,
            current_user=user,
            db=db
        )
        
        assert response.token is not None
        print(f"Success! Token: {response.token}")
