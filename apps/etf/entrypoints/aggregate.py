import asyncio

import pandas as pd


async def main():
    aggregated_df = pd.DataFrame(columns=["symbol", "yield_amount"])
    yield_df = pd.read_csv("apps/etf/build/yield.csv")
    yield_df = yield_df.sort_values(by=["symbol", "utc_time"])
    aggregated_df = (
        yield_df.groupby("symbol")["yield_amount"]
        .apply(lambda x: ",".join(x.astype(str)))
        .reset_index()
    )
    aggregated_df = aggregated_df.sort_values(by=["symbol"], ascending=[False])
    aggregated_df.to_csv("apps/etf/build/aggregated.csv", index=False)


asyncio.run(main())
