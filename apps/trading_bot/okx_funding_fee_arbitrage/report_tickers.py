from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil
from typing import Mapping

import ccxt.pro
import numpy as np
import pandas as pd
from httpx import AsyncClient

from apps.trading_bot.okx_funding_fee_arbitrage.number import decimalize


async def get_discount_rate_map(source: str) -> Mapping[str, Decimal]:
    async with AsyncClient() as client:
        response = await client.get(source)
        response_json = response.json()
    discount_rate_map = {}
    for discount_class in response_json["data"]:
        coins = discount_class["coins"].split("、")
        rate = discount_class["rateInfos"][0]["discountRate"]
        for symbol in coins:
            discount_rate_map[symbol] = decimalize(rate)
    return discount_rate_map


async def get_tickers_df(
    exchange: ccxt.pro.okx, discount_rate_map: Mapping[str, Decimal], window_size: int
) -> pd.DataFrame:
    records = []

    weights = np.arange(window_size)
    since = int(
        (datetime.now() - timedelta(days=ceil(window_size / 3))).timestamp() * 1000
    )

    i = 0
    symbol_to_market_map = await exchange.load_markets()
    for market in symbol_to_market_map.values():
        if not market["swap"]:
            continue
        if not market["quote"] == "USDT":
            continue
        base = market["base"]
        spot_symbol = f"{base}/{market['quote']}"
        if symbol_to_market_map.get(spot_symbol) is None:
            continue

        i += 1
        symbol = market["symbol"]
        print(f"#{i} - {symbol}...")
        latest_funding_rate = await exchange.fetch_funding_rate(symbol=symbol)
        past_funding_rate_histories = await exchange.fetch_funding_rate_history(
            symbol=symbol, since=since, limit=window_size + 3
        )

        funding_rate_histories = [*past_funding_rate_histories, latest_funding_rate]
        funding_rates = np.asarray(
            [frh["fundingRate"] for frh in funding_rate_histories[-window_size:]],
            dtype=np.float32,
        )
        if len(funding_rates) != window_size:
            continue
        positive_count = np.count_nonzero(funding_rates > 0)
        negative_count = np.count_nonzero(funding_rates < 0)
        positive_rate = positive_count / (positive_count + negative_count)
        negative_rate = negative_count / (positive_count + negative_count)
        avg_funding_rate_8h = np.average(funding_rates, weights=weights)

        discount_rate = float(discount_rate_map.get(base, Decimal("0")))
        records.append(
            {
                "symbol": symbol,
                "discount_rate": discount_rate,
                "funding_rate_annum": avg_funding_rate_8h * 3 * 365,
                "avg_funding_rate": avg_funding_rate_8h,
                "positive_rate": positive_rate,
                "negative_rate": negative_rate,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "funding_rates": funding_rates.tolist(),
            }
        )
    tickers_df = pd.DataFrame(records)
    tickers_df = tickers_df.sort_values(
        by=["discount_rate", "positive_rate", "avg_funding_rate"],
        ascending=[False, False, False],
    )
    return tickers_df
