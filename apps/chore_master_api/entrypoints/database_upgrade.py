import asyncio

from apps.chore_master_api.service_layers.database import upgrade


async def main():
    await upgrade()


if __name__ == "__main__":
    asyncio.run(main())
