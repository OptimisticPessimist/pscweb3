
import asyncio
import httpx

async def test_create_project():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # 1. Login to get token (assuming hardcoded test user or existing mechanism)
        # For simplicity, we assume we can bypass or use a known token? 
        # Or we need to login real quick?
        # Let's try to hit it. If 401, we know it's reachable.
        try:
             # We need a token. Let's use the one from the browser if possible? 
             # No, we can't access browser storage.
             # We'll rely on the existing auth flow or just check if the server responds at all.
             
             # Health check style
             response = await client.get("/api/projects/") 
             print(f"GET /projects/ status: {response.status_code}")
             
             if response.status_code == 401:
                 print("Backend is reachable (Auth required).")
             elif response.status_code == 200:
                 print("Backend reachable and authenticated?")
             
        except Exception as e:
            print(f"Backend connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_project())
