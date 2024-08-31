import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import TypedDict, get_type_hints

import pandas as pd


class Yield(TypedDict):
    symbol: str
    utc_time: datetime
    yield_amount: Decimal


async def process_dividend(yield_df: pd.DataFrame) -> pd.DataFrame:
    input_root_file_path = "apps/etf/data/dividend.csv"
    dividend_df = pd.read_csv(input_root_file_path)

    def _get_utc_time(raw_time: str) -> datetime:
        year = int(raw_time[:3]) + 1911
        month = int(raw_time[4:6])
        day = int(raw_time[7:9])
        dt = datetime(year, month, day).astimezone(tz=timezone.utc)
        return dt

    for _i, row in dividend_df.iterrows():
        raw_yield_amount = row["收益分配金額 (每1受益權益單位)"]
        if pd.isna(raw_yield_amount):
            continue
        yield_df.loc[len(yield_df)] = {
            "symbol": row["證券代號"],
            "utc_time": _get_utc_time(row["除息交易日"]),
            "yield_amount": Decimal(str(raw_yield_amount)).normalize(),
        }


async def main():
    yield_df = pd.DataFrame(columns=get_type_hints(Yield).keys())
    await process_dividend(yield_df)
    yield_df = yield_df.sort_values(by=["utc_time", "symbol"], ascending=[False, False])
    yield_df.to_csv("apps/etf/build/yield.csv", index=False)


asyncio.run(main())
