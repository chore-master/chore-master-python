import asyncio

from apps.chore_master_api.service_layers.database import import_data


async def main():
    await import_data()


if __name__ == "__main__":
    asyncio.run(main())
