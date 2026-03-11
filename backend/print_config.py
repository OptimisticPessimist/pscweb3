import asyncio

from src.services.premium_config import PremiumConfigService


async def main():
    config = await PremiumConfigService.get_config()
    print("CURRENT CONFIG:")
    print(config)


if __name__ == "__main__":
    asyncio.run(main())
