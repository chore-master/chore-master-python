import asyncio
import os
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from typing import TypedDict, get_type_hints
from uuid import uuid4

import pandas as pd
from bs4 import BeautifulSoup as bs


class Bill(TypedDict):
    reference: str
    session_reference: str
    utc_time: str
    account_reference: str
    transaction_type: str
    bill_type: str
    amount_change: Decimal
    instrument_reference: str
    order_reference: str


async def process_capital_securities_corp(bill_df: pd.DataFrame) -> pd.DataFrame:
    ACCOUNT_REFERENCE = "群益證券"

    def get_normalized_symbol(raw: str) -> str:
        symbol = (
            raw.replace(" ", "")
            .replace("0056高股息", "0056元大高股息")
            .replace("2006東鋼", "2006東和鋼鐵")
        )
        if symbol == "00692富邦公":
            symbol = "00692富邦公司治理"
        elif symbol == "00710B復華彭":
            symbol = "00710B復華彭博非投等債"
        elif symbol == "00850元大臺":
            symbol = "00850元大臺灣ESG永續"
        elif symbol == "00850元大臺":
            symbol = "00850元大臺灣ESG永續"
        elif symbol == "00888永豐台":
            symbol = "00888永豐台灣ESG"
        elif symbol == "00891中信關":
            symbol = "00891中信關鍵半導體"
        elif symbol == "00730富邦臺":
            symbol = "00730富邦臺灣優質高息"
        return symbol

    def get_utc_time(raw: str) -> str:
        local_date = raw.replace("/", "-")
        dt = datetime.strptime(f"{local_date}T00:00:00+08:00", "%Y-%m-%dT%H:%M:%S%z")
        utc_time = dt.astimezone(tz=timezone.utc).isoformat()
        return utc_time

    input_root_dir_path = "apps/bill_processor/data/capital_securities_corp"
    filtered_years = [
        year
        for year in os.listdir(input_root_dir_path)
        if os.path.isdir(os.path.join(input_root_dir_path, year))
    ]
    sorted_years = sorted(filtered_years, key=lambda x: int(x))
    for year in sorted_years:
        year_dir_path = os.path.join(input_root_dir_path, year)
        file_names = os.listdir(year_dir_path)
        filtered_file_names = [
            file_name
            for file_name in file_names
            if os.path.isfile(os.path.join(year_dir_path, file_name))
            and file_name.endswith(".xls")
        ]
        sorted_file_names = sorted(
            filtered_file_names, key=lambda x: int(x.split(".")[0][7:])
        )
        for file_name in sorted_file_names:
            file_path = os.path.join(year_dir_path, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
                soup = bs(html_content, "html.parser")
            ths = soup.find_all("th", string="股票名稱")
            for th in ths:
                pnl_table = th.parent.parent
                sell_table = pnl_table.find_next("table")
                _, sell_table_header_tr, *sell_table_body_trs = sell_table.find_all(
                    "tr", recursive=False
                )
                sell_df = pd.read_html(
                    StringIO(
                        f"<table><thead>{str(sell_table_header_tr)}</thead><tbody>{str(sell_table_body_trs)}</tbody></table>"
                    )
                )[0]
                buy_table = sell_table.find_next("table")
                _, buy_table_header_tr, *buy_table_body_trs = buy_table.find_all(
                    "tr", recursive=False
                )
                buy_df = pd.read_html(
                    StringIO(
                        f"<table><thead>{str(buy_table_header_tr)}</thead><tbody>{str(buy_table_body_trs)}</tbody></table>"
                    )
                )[0]

                session_reference = str(uuid4())

                for _i, row in buy_df.iterrows():
                    symbol = get_normalized_symbol(row.iloc[0])
                    utc_time = get_utc_time(row.iloc[1])
                    order_reference = row.iloc[2]
                    amount = Decimal(row.iloc[4])
                    notional = Decimal(row.iloc[6])
                    fee = Decimal(row.iloc[7])
                    tax = Decimal(row.iloc[8])
                    bill_df.loc[len(bill_df)] = {
                        "reference": str(uuid4()),
                        "session_reference": session_reference,
                        "utc_time": utc_time,
                        "account_reference": ACCOUNT_REFERENCE,
                        "transaction_type": "trade",
                        "bill_type": "sell",
                        "amount_change": -notional,
                        "instrument_reference": "TWD",
                        "order_reference": order_reference,
                    }
                    bill_df.loc[len(bill_df)] = {
                        "reference": str(uuid4()),
                        "session_reference": session_reference,
                        "utc_time": utc_time,
                        "account_reference": ACCOUNT_REFERENCE,
                        "transaction_type": "trade",
                        "bill_type": "buy",
                        "amount_change": amount,
                        "instrument_reference": symbol,
                        "order_reference": order_reference,
                    }
                    if fee > 0:
                        bill_df.loc[len(bill_df)] = {
                            "reference": str(uuid4()),
                            "session_reference": session_reference,
                            "utc_time": utc_time,
                            "account_reference": ACCOUNT_REFERENCE,
                            "transaction_type": "trade",
                            "bill_type": "fee",
                            "amount_change": -fee,
                            "instrument_reference": "TWD",
                            "order_reference": order_reference,
                        }
                    if tax > 0:
                        bill_df.loc[len(bill_df)] = {
                            "reference": str(uuid4()),
                            "session_reference": session_reference,
                            "utc_time": utc_time,
                            "account_reference": ACCOUNT_REFERENCE,
                            "transaction_type": "trade",
                            "bill_type": "tax",
                            "amount_change": -tax,
                            "instrument_reference": "TWD",
                            "order_reference": order_reference,
                        }

                for _i, row in sell_df.iterrows():
                    symbol = get_normalized_symbol(row.iloc[0])
                    utc_time = get_utc_time(row.iloc[1])
                    order_reference = row.iloc[2]
                    amount = Decimal(row.iloc[4])
                    notional = Decimal(row.iloc[6])
                    fee = Decimal(row.iloc[7])
                    tax = Decimal(row.iloc[8])
                    bill_df.loc[len(bill_df)] = {
                        "reference": str(uuid4()),
                        "session_reference": session_reference,
                        "utc_time": utc_time,
                        "account_reference": ACCOUNT_REFERENCE,
                        "transaction_type": "trade",
                        "bill_type": "sell",
                        "amount_change": -amount,
                        "instrument_reference": symbol,
                        "order_reference": order_reference,
                    }
                    bill_df.loc[len(bill_df)] = {
                        "reference": str(uuid4()),
                        "session_reference": session_reference,
                        "utc_time": utc_time,
                        "account_reference": ACCOUNT_REFERENCE,
                        "transaction_type": "trade",
                        "bill_type": "buy",
                        "amount_change": notional,
                        "instrument_reference": "TWD",
                        "order_reference": order_reference,
                    }
                    if fee > 0:
                        bill_df.loc[len(bill_df)] = {
                            "reference": str(uuid4()),
                            "session_reference": session_reference,
                            "utc_time": utc_time,
                            "account_reference": ACCOUNT_REFERENCE,
                            "transaction_type": "trade",
                            "bill_type": "fee",
                            "amount_change": -fee,
                            "instrument_reference": "TWD",
                            "order_reference": order_reference,
                        }
                    if tax > 0:
                        bill_df.loc[len(bill_df)] = {
                            "reference": str(uuid4()),
                            "session_reference": session_reference,
                            "utc_time": utc_time,
                            "account_reference": ACCOUNT_REFERENCE,
                            "transaction_type": "trade",
                            "bill_type": "tax",
                            "amount_change": -tax,
                            "instrument_reference": "TWD",
                            "order_reference": order_reference,
                        }


async def main():
    bill_df = pd.DataFrame(columns=get_type_hints(Bill).keys())
    await process_capital_securities_corp(bill_df)
    bill_df = bill_df.sort_values(by=["utc_time"], ascending=[True])
    bill_df.to_csv("apps/bill_processor/build/result.csv", index=False)


asyncio.run(main())