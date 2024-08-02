import asyncio

import pandas as pd
from httpx import AsyncClient


async def main():
    async with AsyncClient() as client:
        response = await client.get(
            "https://www.twse.com.tw/rwd/zh/ETF/etfDiv",
            params={
                "stkNo": "",
                "startDate": "20050101",
                "endDate": "20240802",
                "response": "json",
            },
        )
        response_dict = response.json()
        fields = response_dict["fields"]
        entries = response_dict["data"]
    entry_df = pd.DataFrame(data=entries, columns=fields)
    entry_df.to_csv("apps/etf/data/entry.csv", index=False)


asyncio.run(main())
