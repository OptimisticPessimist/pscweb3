"""Discord認証ヘルパースクリプト."""

import asyncio
import json
import sys

import httpx


async def exchange_token(token_endpoint, data):
    """Discordアクセストークンとユーザー情報を交換する."""
    try:
        async with httpx.AsyncClient() as client:
            # 1. トークン取得
            resp = await client.post(
                token_endpoint,
                data=data,
                timeout=10.0
            )
            if resp.status_code >= 400:
                with open(result_file_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "status_code": resp.status_code,
                        "body": resp.json(),
                        "step": "token_exchange"
                    }, f)
                return

            token_data = resp.json()
            access_token = token_data.get("access_token")

            if not access_token:
                with open(result_file_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "error": "No access token in response",
                        "body": token_data
                    }, f)
                return

            # 2. ユーザー情報取得
            user_resp = await client.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )

            if user_resp.status_code >= 400:
                 with open(result_file_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "status_code": user_resp.status_code,
                        "body": user_resp.json(),
                        "step": "user_info"
                    }, f)
                 return

            # 成功！トークンとユーザー情報をまとめて返す
            result_data = {
                "status_code": 200,
                "token": token_data,
                "user": user_resp.json()
            }
            with open(result_file_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f)

    except Exception as e:
        import traceback
        err_data = {
            "error": str(e),
            "trace": traceback.format_exc()
        }
        with open(result_file_path, "w", encoding="utf-8") as f:
            json.dump(err_data, f)

if __name__ == "__main__":
    if len(sys.argv) < 7:
        sys.exit(1)

    result_file_path = sys.argv[1]
    endpoint = sys.argv[2]

    data = {
        'grant_type': 'authorization_code',
        'client_id': sys.argv[3],
        'client_secret': sys.argv[4],
        'redirect_uri': sys.argv[5],
        'code': sys.argv[6]
    }

    asyncio.run(exchange_token(endpoint, data))
