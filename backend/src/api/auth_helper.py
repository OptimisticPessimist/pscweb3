import asyncio
import json
import sys

import httpx


async def exchange_token(token_endpoint, data):
    max_retries = 3
    try:
        async with httpx.AsyncClient() as client:
            # 1. トークン取得 (リトライ付き)
            token_data = None
            for i in range(max_retries + 1):
                resp = await client.post(token_endpoint, data=data, timeout=15.0)
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", 2 ** (i + 1)))
                    # ヘルパーは標準出力で進捗を出さない設計なのでログ記録は困難だが、待機は実行する
                    await asyncio.sleep(retry_after)
                    continue

                if resp.status_code >= 400:
                    with open(result_file_path, "w", encoding="utf-8") as f:
                        json.dump(
                            {
                                "status_code": resp.status_code,
                                "body": resp.json()
                                if resp.headers.get("content-type") == "application/json"
                                else resp.text,
                                "step": "token_exchange",
                                "headers": dict(resp.headers),
                            },
                            f,
                        )
                    return

                token_data = resp.json()
                break

            if not token_data:
                # このケースは通常resp.status_codeが400以上でリターンされているはずだが、念のため
                return

            access_token = token_data.get("access_token")
            if not access_token:
                with open(result_file_path, "w", encoding="utf-8") as f:
                    json.dump({"error": "No access token in response", "body": token_data}, f)
                return

            # 2. ユーザー情報取得 (リトライ付き)
            user_data = None
            for i in range(max_retries + 1):
                user_resp = await client.get(
                    "https://discord.com/api/v10/users/@me",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=15.0,
                )
                if user_resp.status_code == 429:
                    retry_after = float(user_resp.headers.get("Retry-After", 2 ** (i + 1)))
                    await asyncio.sleep(retry_after)
                    continue

                if user_resp.status_code >= 400:
                    with open(result_file_path, "w", encoding="utf-8") as f:
                        json.dump(
                            {
                                "status_code": user_resp.status_code,
                                "body": user_resp.json()
                                if user_resp.headers.get("content-type") == "application/json"
                                else user_resp.text,
                                "step": "user_info",
                                "headers": dict(user_resp.headers),
                            },
                            f,
                        )
                    return

                user_data = user_resp.json()
                break

            # 成功！トークンとユーザー情報をまとめて返す
            result_data = {"status_code": 200, "token": token_data, "user": user_data}
            with open(result_file_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f)

    except Exception as e:
        import traceback

        err_data = {"error": str(e), "trace": traceback.format_exc()}
        with open(result_file_path, "w", encoding="utf-8") as f:
            json.dump(err_data, f)


if __name__ == "__main__":
    if len(sys.argv) < 7:
        sys.exit(1)

    result_file_path = sys.argv[1]
    endpoint = sys.argv[2]

    data = {
        "grant_type": "authorization_code",
        "client_id": sys.argv[3],
        "client_secret": sys.argv[4],
        "redirect_uri": sys.argv[5],
        "code": sys.argv[6],
    }

    asyncio.run(exchange_token(endpoint, data))
