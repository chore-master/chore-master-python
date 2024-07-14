import asyncio
import json

from httpx import AsyncClient


async def async_handler(event, context):
    async with AsyncClient() as client:
        response = await client.get("https://api.coindesk.com/v1/bpi/currentprice.json")
        response_dict = print(response.json())
    return {
        "statusCode": 200,
        "body": json.dumps(response_dict),
    }


def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_handler(event, context))
