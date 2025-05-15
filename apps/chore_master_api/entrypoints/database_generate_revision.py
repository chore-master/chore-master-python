import asyncio

from apps.chore_master_api.service_layers.database import generate_revision


async def main():
    await generate_revision()


if __name__ == "__main__":
    asyncio.run(main())
