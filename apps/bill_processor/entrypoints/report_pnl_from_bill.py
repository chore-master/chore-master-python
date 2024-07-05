import asyncio
import os

import pandas as pd


async def main():
    input_root_dir_path = "apps/bill_processor/build"
    file_path = os.path.join(input_root_dir_path, "bill.csv")
    bill_df = pd.read_csv(file_path)

    bill_df["cumulative_sum"] = bill_df.groupby(["session_reference", "symbol"])[
        "amount_change"
    ].cumsum()
    bill_df["_utc_time"] = pd.to_datetime(bill_df["utc_time"])

    grouped = bill_df.groupby(["session_reference", "symbol"])
    aggregated_df = grouped.agg(
        start_time=("_utc_time", "min"),
        end_time=("_utc_time", "max"),
        min_balance_amount=("cumulative_sum", "min"),
        max_balance_amount=("cumulative_sum", "max"),
        balance_amount=("amount_change", "sum"),
    ).reset_index()
    aggregated_df["timedelta_in_days"] = (
        aggregated_df["end_time"] - aggregated_df["start_time"]
    ).dt.days
    aggregated_df = aggregated_df.sort_values(
        by=["start_time", "end_time"], ascending=[True, True]
    )
    aggregated_df.to_csv(
        "apps/bill_processor/build/pnl.csv",
        columns=[
            "session_reference",
            "start_time",
            "end_time",
            "timedelta_in_days",
            "min_balance_amount",
            "max_balance_amount",
            "balance_amount",
            "symbol",
        ],
        index=False,
    )


asyncio.run(main())
