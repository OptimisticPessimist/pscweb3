import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_test_project_and_invitation():
    if not DATABASE_URL:
        print("No DATABASE_URL found.")
        return

    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0
        }
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # First find a user to own the project (just pick the first one)
        stmt_user = text("SELECT id FROM users LIMIT 1")
        result_user = await session.execute(stmt_user)
        user_id = result_user.scalar()
        
        if not user_id:
            print("No users found in the database. Cannot create a project.")
            return

        # 1. Create a dummy project
        project_id = str(uuid.uuid4())
        stmt_project = text("""
            INSERT INTO projects (id, owner_id, name, created_at, updated_at)
            VALUES (:id, :owner_id, :name, :now, :now)
        """)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.execute(stmt_project, {
            "id": project_id,
            "owner_id": user_id,
            "name": "TEST_AUTO_RETRY_PROJECT",
            "now": now
        })
        
        # 2. Add owner to project_members
        stmt_member = text("""
            INSERT INTO project_members (id, project_id, user_id, role, joined_at)
            VALUES (:id, :project_id, :user_id, 'owner', :now)
        """)
        await session.execute(stmt_member, {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "now": now
        })

        # 3. Create an invitation token for this project
        import secrets
        token = secrets.token_urlsafe(32)
        stmt_inv = text("""
            INSERT INTO project_invitations (id, project_id, token, role, created_at, expires_at)
            VALUES (:id, :project_id, :token, 'member', :now, :expires)
        """)
        expires = now + timedelta(days=7)
        await session.execute(stmt_inv, {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "token": token,
            "now": now,
            "expires": expires.replace(tzinfo=None)
        })

        await session.commit()
        
        print("\n--- TEST INVITATION CREATED SUCCESSFULLY ---")
        print(f"Project Name: TEST_AUTO_RETRY_PROJECT")
        print(f"Invitation URL: https://ashy-river-0227e1e00.3.azurestaticapps.net/invitations/{token}")
        print("--------------------------------------------\n")
        print("Please click the link above and test the login flow.")

if __name__ == "__main__":
    asyncio.run(create_test_project_and_invitation())
