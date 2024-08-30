import asyncio
from datetime import datetime
from typing import AsyncIterator

import ccxt.pro


async def fetch_max_3month_bill_history(
    exchange: ccxt.pro.okx, since_datetime: datetime, until_datetime: datetime
) -> AsyncIterator[dict]:
    # https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bills-details-last-7-days
    # https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bills-details-last-3-months
    since = int(since_datetime.timestamp() * 1000)
    until = int(until_datetime.timestamp() * 1000)
    while True:
        response = await exchange.private_get_account_bills_archive(
            params={
                "begin": since,
                "end": until,
            }
        )
        all_entries = response["data"]
        if len(all_entries) == 0:
            break
        mapped_entries = []
        for entry in all_entries:
            timestamp = exchange.safe_integer(entry, "ts")
            currency_id = exchange.safe_string(entry, "ccy")
            currency = exchange.safe_currency_code(currency_id)
            common_attrs = {
                "info": entry,
                "timestamp": timestamp,
                "datetime": exchange.iso8601(timestamp),
                "id": exchange.safe_string(entry, "billId"),
                "currency": currency,
            }
            if entry["type"] == "2":
                instId = exchange.safe_string(entry, "instId")
                marketInner = exchange.safe_market(instId)
                sub_type_to_side_map = {
                    "1": "buy",
                    "2": "sell",
                }
                mapped_entries.append(
                    {
                        **common_attrs,
                        "type": "trade_fee",
                        "balance_change": exchange.safe_number(entry, "fee"),
                        "symbol": marketInner["symbol"],
                        "side": sub_type_to_side_map[entry["subType"]],
                    }
                )
            elif entry["type"] == "7":
                mapped_entries.append(
                    {
                        **common_attrs,
                        "type": "interest_deduction",
                        "balance_change": exchange.safe_number(entry, "balChg"),
                        "currency": entry["ccy"],
                    }
                )
            elif entry["type"] == "8":
                instId = exchange.safe_string(entry, "instId")
                marketInner = exchange.safe_market(instId)
                mapped_entries.append(
                    {
                        **common_attrs,
                        "type": "funding_fee",
                        "balance_change": exchange.safe_number(entry, "balChg"),
                        "symbol": marketInner["symbol"],
                    }
                )
        sorted_mapped_entries = exchange.sort_by(mapped_entries, "timestamp")
        for entry in sorted_mapped_entries:
            yield entry
        max_timestamp_entry = max(
            all_entries, key=lambda entry: exchange.safe_integer(entry, "ts")
        )
        since = exchange.safe_integer(max_timestamp_entry, "ts") + 1
        await asyncio.sleep(0.4)


# async def fetch_borrow_interest(
#     exchange: ccxt.pro.okx, since_datetime: datetime, until_datetime: datetime
# ) -> AsyncIterator[dict]:
#     since = int(since_datetime.timestamp() * 1000)
#     until = int(until_datetime.timestamp() * 1000)
#     while True:
#         sorted_entries = await exchange.fetch_borrow_interest(
#             since=since, params={"before": until}
#         )
#         if len(sorted_entries) == 0:
#             break
#         for entry in sorted_entries:
#             yield entry
#         since = sorted_entries[-1]["timestamp"] + 1
