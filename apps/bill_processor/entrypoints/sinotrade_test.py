import asyncio

import shioaji as sj

from modules.base.env import get_env


async def main():
    print(sj.__version__)

    api = sj.Shioaji(simulation=True)
    accounts = api.login(api_key=get_env("API_KEY"), secret_key=get_env("SECRET_KEY"))
    contract = api.Contracts.Stocks.TSE["2890"]

    # 證券委託單 - 請修改此處
    order = api.Order(
        price=25,  # 價格
        quantity=1,  # 數量
        action=sj.constant.Action.Buy,  # 買賣別
        price_type=sj.constant.StockPriceType.LMT,  # 委託價格類別
        order_type=sj.constant.OrderType.ROD,  # 委託條件
        account=api.stock_account,  # 下單帳號
    )

    # 下單
    trade = api.place_order(contract, order)
    trade


asyncio.run(main())
