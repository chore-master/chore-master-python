import asyncio
import os
from decimal import Decimal
from typing import TypedDict, get_type_hints
from uuid import uuid4

import pandas as pd


class ProfitAndLoss(TypedDict):
    reference: str
    session_reference: str
    start_time: str
    end_time: str
    timedelta_in_days: int
    cost_amount: Decimal
    revenue_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    pnl_amount: Decimal
    symbol: str
    return_rate: Decimal
    apr: Decimal
    max_equity_amount: Decimal
    min_equity_amount: Decimal


async def aggregate_pnl(bill_df: pd.DataFrame):
    aggregated_df = pd.DataFrame(columns=get_type_hints(ProfitAndLoss).keys())
    grouped_by_session_reference = bill_df.groupby(["session_reference"])
    for (session_reference,), session_df in grouped_by_session_reference:
        grouped_by_symbol = session_df.groupby(["symbol"])
        session_df["_utc_time"] = pd.to_datetime(session_df["utc_time"])
        start_time = session_df["_utc_time"].min()
        end_time = session_df["_utc_time"].max()
        timedelta_in_days = (end_time - start_time).days

        for (symbol,), symbol_df in grouped_by_symbol:
            time_df = (
                symbol_df.groupby(["utc_time"])["amount_change"].sum().reset_index()
            ).sort_values(by=["utc_time"], ascending=[True])
            time_df["equity_amount"] = time_df["amount_change"].cumsum()
            sell_amount_change = Decimal(
                symbol_df[
                    (symbol_df["bill_type"] == "sell") & (symbol_df["symbol"] == symbol)
                ]["amount_change"]
                .sum()
                .item()
            )
            buy_amount_change = Decimal(
                symbol_df[
                    (symbol_df["bill_type"] == "buy") & (symbol_df["symbol"] == symbol)
                ]["amount_change"]
                .sum()
                .item()
            )
            fee_amount_change = Decimal(
                symbol_df[
                    (symbol_df["bill_type"] == "fee") & (symbol_df["symbol"] == symbol)
                ]["amount_change"]
                .sum()
                .item()
            )
            tax_amount_change = Decimal(
                symbol_df[
                    (symbol_df["bill_type"] == "tax") & (symbol_df["symbol"] == symbol)
                ]["amount_change"]
                .sum()
                .item()
            )
            pnl_amount = (
                buy_amount_change
                + sell_amount_change
                + fee_amount_change
                + tax_amount_change
            )
            max_equity_amount = Decimal(time_df["equity_amount"].max().item())
            min_equity_amount = Decimal(time_df["equity_amount"].min().item())
            cost_amount = -sell_amount_change
            if cost_amount == 0:
                return_rate = None
                apr = None
            else:
                return_rate = (pnl_amount / cost_amount).quantize(Decimal("0.0001"))
                apr = ((return_rate / timedelta_in_days) * 365).quantize(
                    Decimal("0.0001")
                )
            aggregated_df.loc[len(aggregated_df)] = {
                "reference": str(uuid4()),
                "session_reference": session_reference,
                "start_time": start_time,
                "end_time": end_time,
                "timedelta_in_days": timedelta_in_days,
                "cost_amount": cost_amount,
                "revenue_amount": buy_amount_change,
                "fee_amount": -fee_amount_change,
                "tax_amount": -tax_amount_change,
                "pnl_amount": pnl_amount,
                "symbol": symbol,
                "return_rate": return_rate,
                "apr": apr,
                "max_equity_amount": max_equity_amount,
                "min_equity_amount": min_equity_amount,
            }
    aggregated_df = aggregated_df.sort_values(
        by=["start_time", "end_time"], ascending=[False, False]
    )
    aggregated_df.to_csv("apps/bill_processor/build/pnl.csv", index=False)


async def main():
    input_root_dir_path = "apps/bill_processor/build"
    file_path = os.path.join(input_root_dir_path, "bill.csv")
    bill_df = pd.read_csv(file_path)
    await aggregate_pnl(bill_df)


asyncio.run(main())
