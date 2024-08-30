from datetime import datetime
from typing import Literal, Optional

import ccxt.pro
import pandas as pd

from apps.trading_bot.okx_funding_fee_arbitrage.pagination import (
    fetch_max_3month_bill_history,
)


async def get_cash_flow_df_and_fee_balance_df(
    exchange: ccxt.pro.okx,
    account: Literal["trading"],
    since_fee_balance_df: pd.DataFrame,
    since_datetime: datetime,
    until_datetime: datetime,
) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    records = []

    # deposits = exchange.fetch_deposits()
    # withdrawals = exchange.fetch_withdrawals()

    # transfers = await exchange.fetch_transfers()
    # for transfer in transfers:
    #     if transfer["fromAccount"] == account:
    #         flow_amount = -transfer["amount"]
    #     elif transfer["toAccount"] == account:
    #         flow_amount = transfer["amount"]
    #     records.append(
    #         {
    #             "timestamp": transfer["timestamp"],
    #             "datetime": transfer["datetime"],
    #             "type": f"transfer {transfer['fromAccount']} -> {transfer['toAccount']}",
    #             "flow_amount": flow_amount,
    #             "currency": transfer["currency"],
    #         }
    #     )

    # trades = await exchange.fetch_my_trades()
    # for trade in trades:
    #     if trade["side"] == "buy":
    #         in_currency, out_currency = trade["symbol"].split("/")
    #         records.extend(
    #             [
    #                 {
    #                     "timestamp": trade["timestamp"],
    #                     "datetime": trade["datetime"],
    #                     "type": f"{trade['side']} {trade['symbol']} (income)",
    #                     "flow_amount": trade["amount"],
    #                     "currency": in_currency,
    #                 },
    #                 {
    #                     "timestamp": trade["timestamp"],
    #                     "datetime": trade["datetime"],
    #                     "type": f"{trade['side']} {trade['symbol']} (cost)",
    #                     "flow_amount": -trade["cost"],
    #                     "currency": out_currency,
    #                 },
    #             ]
    #         )
    #     elif trade["side"] == "sell":
    #         out_currency, in_currency = trade["symbol"].split("/")
    #         records.extend(
    #             [
    #                 {
    #                     "timestamp": trade["timestamp"],
    #                     "datetime": trade["datetime"],
    #                     "type": f"{trade['side']} {trade['symbol']} (income)",
    #                     "flow_amount": trade["cost"],
    #                     "currency": in_currency,
    #                 },
    #                 {
    #                     "timestamp": trade["timestamp"],
    #                     "datetime": trade["datetime"],
    #                     "type": f"{trade['side']} {trade['symbol']} (cost)",
    #                     "flow_amount": -trade["amount"],
    #                     "currency": out_currency,
    #                 },
    #             ]
    #         )
    #     records.extend(
    #         [
    #             {
    #                 "timestamp": trade["timestamp"],
    #                 "datetime": trade["datetime"],
    #                 "type": f"{trade['side']} {trade['symbol']} (fee)",
    #                 "flow_amount": -trade["fee"]["cost"],
    #                 "currency": trade["fee"]["currency"],
    #             },
    #         ]
    #     )

    async for bill in fetch_max_3month_bill_history(
        exchange=exchange, since_datetime=since_datetime, until_datetime=until_datetime
    ):
        if bill["type"] == "trade_fee":
            records.append(
                {
                    "timestamp": bill["timestamp"],
                    "datetime": bill["datetime"],
                    "balance_change": bill["balance_change"],
                    "currency": bill["currency"],
                    "summary": f"trade fee expense ({bill['side']} {bill['symbol']})",
                }
            )
        elif bill["type"] == "interest_deduction":
            records.append(
                {
                    "timestamp": bill["timestamp"],
                    "datetime": bill["datetime"],
                    "summary": "interest deduction",
                    "balance_change": bill["balance_change"],
                    "currency": bill["currency"],
                }
            )
        elif bill["type"] == "funding_fee":
            records.append(
                {
                    "timestamp": bill["timestamp"],
                    "datetime": bill["datetime"],
                    "summary": f"funding fee expense/income ({bill['symbol']})",
                    "balance_change": bill["balance_change"],
                    "currency": bill["currency"],
                }
            )

    # async for borrow_cost in fetch_borrow_interest(
    #     exchange=exchange, since_datetime=since_datetime, until_datetime=until_datetime
    # ):
    #     records.append(
    #         {
    #             "timestamp": borrow_cost["timestamp"],
    #             "datetime": borrow_cost["datetime"],
    #             "type": "pay borrow interest",
    #             "flow_amount": -borrow_cost["interest"],
    #             "currency": borrow_cost["currency"],
    #         }
    #     )

    if len(records) == 0:
        return None, None

    cash_flow_df = pd.DataFrame(records)
    cash_flow_df = cash_flow_df.sort_values(by="timestamp", ascending=True)
    cash_flow_df["balance"] = cash_flow_df.groupby("currency")[
        "balance_change"
    ].cumsum()
    currency_to_balance_map = {}
    for _index, row in since_fee_balance_df.iterrows():
        currency_to_balance_map[row["currency"]] = row["balance"]
        cash_flow_df.loc[cash_flow_df["currency"] == row["currency"], "balance"] += row[
            "balance"
        ]

    affected_fee_balance_df = cash_flow_df.loc[
        cash_flow_df.groupby("currency")["timestamp"].idxmax()
    ]
    for _index, row in affected_fee_balance_df.iterrows():
        currency_to_balance_map[row["currency"]] = row["balance"]
    fee_balance_df = pd.DataFrame(
        {
            "currency": currency_to_balance_map.keys(),
            "balance": currency_to_balance_map.values(),
        }
    )

    return cash_flow_df, fee_balance_df
