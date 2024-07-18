import asyncio

import pandas as pd
import shioaji as sj

from modules.base.env import get_env


async def main():
    # sinotrade.github.io/zh_tw
    api = sj.Shioaji()
    api.login(api_key=get_env("API_KEY"), secret_key=get_env("SECRET_KEY"))
    balance = api.account_balance()
    profit_losses = api.list_profit_loss(api.stock_account, "2024-01-01", "2025-01-01")
    print(balance)

    profit_loss_details = []
    for profit_loss in profit_losses:
        profit_loss_detail = api.list_profit_loss_detail(
            api.stock_account, profit_loss.id
        )
        profit_loss_details.extend(profit_loss_detail)
    bill_df = pd.DataFrame(pnl.__dict__ for pnl in profit_loss_details)
    bill_df.to_csv("apps/bill_processor/build/bill_sinotrade.csv", index=False)


asyncio.run(main())
