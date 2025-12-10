
import asyncio

import httpx


async def test_live_create():
    # Attempt to hit the endpoint. We need a token.
    # Since we can't easily login without credentials, we might need to "cheat" or assume the server allows auth bypass in dev?
    # No, it checks Depends(get_current_user).

    # We can create a token if we have the secret key?
    # backend/src/config.py says default is "test-secret-key-for-testing".

    from datetime import datetime, timedelta

    from jose import jwt
    from sqlalchemy import select

    from src.config import settings  # Import settings

    # We need a valid user ID. UUID.
    # We can pick one from the DB using get_db or just generate one and hope user auto-creation exists (it doesn't).
    # We need a user that exists.
    # Let's verify schema script to print users first?
    # Or just use the debug script approach to find a user, THEN hit the API.
    from src.db import get_db
    from src.db.models import User

    SECRET_KEY = settings.jwt_secret_key # Use correct key
    ALGORITHM = settings.jwt_algorithm

    user_id = None
    async for session in get_db():
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            user_id = str(user.id)
            print(f"Found user: {user.discord_username} {user_id}")
        else:
             print("No users found in DB!")
        break

    if not user_id:
        return

    # Create token
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": user_id}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    headers = {"Authorization": f"Bearer {encoded_jwt}"}

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        print("Sending Create Project request...")
        try:
            response = await client.post(
                "/api/projects/",
                json={"name": "Live Test Project", "description": "Auto test"},
                headers=headers
            )
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Response JSON: {response.json()}")
            except:
                print(f"Response Text: {repr(response.text)}")

            if response.status_code == 200:
                print("SUCCESS: Project created via API.")
            else:
                print("FAILURE: API returned error.")

        except httpx.ReadTimeout:
            print("FAILURE: Request timed out (Backend is hanging).")
        except Exception as e:
             print(f"FAILURE: Request failed: {e}")

if __name__ == "__main__":
    import sys
    # Win32 loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(test_live_create())
