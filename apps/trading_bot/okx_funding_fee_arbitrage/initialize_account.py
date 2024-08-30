import asyncio

import ccxt.pro
from ccxt.base.errors import BadSymbol


async def set_account_configs(exchange: ccxt.pro.okx):
    await exchange.private_post_account_set_isolated_mode(
        params={
            "isoMode": "automatic",
            "type": "MARGIN",
        }
    )
    await exchange.private_post_account_set_auto_loan(
        params={
            "autoLoan": True,
        }
    )
    await exchange.private_post_account_set_position_mode(
        params={
            "posMode": "net_mode",
        }
    )
    await exchange.private_post_account_set_greeks(
        params={
            "greeksType": "BS",
        }
    )


async def set_market_leverages(
    exchange: ccxt.pro.okx, max_margin_leverage: int, max_perp_leverage: int
):
    symbol_to_market_map = await exchange.load_markets()
    processed_margin_currencies = set()
    for market in symbol_to_market_map.values():
        if market["margin"]:
            margin_currency = market["quote"]
            if margin_currency in processed_margin_currencies:
                continue
            processed_margin_currencies.add(margin_currency)
            leverage = min(max_margin_leverage, int(market["info"]["lever"]))
            await exchange.private_post_account_set_leverage(
                params={
                    "ccy": margin_currency,
                    "lever": f"{leverage}",
                    "mgnMode": "cross",
                }
            )
            print(f"Currency {margin_currency} -> {leverage}x")
            await asyncio.sleep(0.33)
        elif market["swap"]:
            leverage = min(max_perp_leverage, int(market["info"]["lever"]))
            try:
                await exchange.private_post_account_set_leverage(
                    params={
                        "instId": market["id"],
                        "lever": f"{leverage}",
                        "mgnMode": "cross",
                    }
                )
            except BadSymbol:
                continue
            print(f"Perp {market['id']} -> {leverage}x")
            await asyncio.sleep(0.33)
