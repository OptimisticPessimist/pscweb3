import asyncio
import httpx
import os
import sys

# Windowsでのイベントループポリシー設定（Python 3.8以降のWindowsではProactorがデフォルトだが念のため）
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def check_connection():
    url = "https://discord.com/api/v10/oauth2/token"
    print(f"Testing connection to {url}...", flush=True)
    
    try:
        async with httpx.AsyncClient() as client:
            # わざとパラメータなしで送って、400 Bad Requestが返ってくるかテスト（通信成立の確認）
            # 接続自体ができなければConnectErrorになる
            resp = await client.post(url, data={
                'grant_type': 'authorization_code',
                'code': 'dummy_code',
                'redirect_uri': 'http://localhost:8000/auth/callback',
                'client_id': 'dummy_id',
                'client_secret': 'dummy_secret'
            })
            print(f"Response Status: {resp.status_code}", flush=True)
            print(f"Response Text: {resp.text[:100]}...", flush=True)
            
            if resp.status_code == 400:
                print("SUCCESS: Connection established (Bad Request is expected for dummy data).", flush=True)
            else:
                print(f"WARNING: Unexpected status code: {resp.status_code}", flush=True)

    except Exception as e:
        print(f"ERROR: Connection failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(check_connection())
    except Exception as e:
        print(f"Fatal Error: {e}")
