import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


async def check_discord_api():
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if not bot_token:
        print("No DISCORD_BOT_TOKEN found in .env")
        return

    url = "https://discord.com/api/v10/users/@me"
    headers = {"Authorization": f"Bot {bot_token}"}

    try:
        async with httpx.AsyncClient() as client:
            print(f"Checking Discord API: {url}")
            response = await client.get(url, headers=headers)
            print(f"Status Code: {response.status_code}")

            # Print rate limit headers
            print("\n--- Rate Limit Headers ---")
            for k, v in response.headers.items():
                if "ratelimit" in k.lower() or "retry-after" in k.lower():
                    print(f"{k}: {v}")

            if response.status_code >= 400:
                print("\n--- Error Response ---")
                print(response.text)
            else:
                print("\n--- Success ---")
                print("Bot Token is valid and working locally.")

    except Exception as e:
        print(f"Error checking Discord API: {e}")


if __name__ == "__main__":
    asyncio.run(check_discord_api())
