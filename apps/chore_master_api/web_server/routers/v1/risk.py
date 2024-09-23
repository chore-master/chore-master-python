import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from math import erf, pi

import ccxt.async_support as ccxt
from fastapi import APIRouter, Body, Depends
from numpy import exp, log, sqrt
from pydantic import BaseModel

from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_api_db,
)
from modules.database.mongo_client import MongoDB
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/risk", tags=["Risk"])


class ReadAbcResponse(BaseModel):
    a: str


class ReadPositionResponse(BaseModel):
    class Position(BaseModel):
        symbol: str
        instrument: str
        account_name: str
        max_leverage: float | None
        side: str
        token_amount: float
        contract_amount: float | None
        liquidation_price: float | None
        entry_price: float | None
        mark_price: float | None
        profit_and_loss: float | None
        realized_pnl: float | None
        unrealized_pnl: float | None
        percentage_to_liquidation: float | None
        current_margin: float | None
        initial_margin: float | None
        maintenance_margin: float | None
        margin_ratio: float | None

    positions: list[Position]


class ReadPositionFxRiskResponse(BaseModel):
    class PositionFxRisk(BaseModel):
        symbol: str
        instrument: str
        base_currency: str
        quote_currency: str
        account_name: str
        side: str
        token_amount: float
        delta: float
        gamma: float
        vega: float
        theta: float

    positions_fx_risk: list[PositionFxRisk]


class ReadPositionIrRiskResponse(BaseModel):
    class PositionIrRisk(BaseModel):
        symbol: str
        instrument: str
        base_currency: str
        quote_currency: str
        account_name: str
        side: str
        token_amount: float
        dv01: float
        rho: float

    positions_ir_risk: list[PositionIrRisk]


class ReadPositionAlertResponse(BaseModel):
    class PositionRiskAlert(BaseModel):
        aggregated_dv01: float
        aggregated_gamma: float
        aggregated_theta: float
        aggregated_vega: float
        aggregated_rho: float
        aggregated_delta: float
        aggregated_profit_and_loss: float

    positions_fx_risk: list[PositionRiskAlert]


@router.get("/abc", response_model=ResponseSchema[ReadAbcResponse])
async def get_some_entities():
    return ResponseSchema(
        status=StatusEnum.SUCCESS, data=ReadAbcResponse(a="some string")
    )


# Define a Pydantic model for the request
class OKXPositionRequest(BaseModel):
    selected_okx_account_names: list[str]


async def get_okx_market_info_by_symbol(symbol: str, exchange: ccxt.okx) -> dict:
    market = await exchange.fetch_markets()
    target_market_list = [m for m in market if m["symbol"] == symbol]
    if target_market_list is None:
        return None
    else:
        target_market = target_market_list[0]
    return target_market


async def get_insturment_by_symbol(symbol: str, exchange: ccxt.okx) -> dict[str, str]:
    target_market = await get_okx_market_info_by_symbol(
        symbol=symbol, exchange=exchange
    )
    if target_market["type"] == "spot":
        instrument = "spot"
    elif target_market["type"] == "future":
        instrument = "future"
    elif target_market["type"] == "option":
        instrument = "option"
    elif target_market["type"] == "swap":
        instrument = "perpetual"
    else:
        instrument = "Not Found"
    return instrument


async def get_currencies_by_symbol(symbol: str, exchange: ccxt.okx) -> tuple[str, str]:
    target_market = await get_okx_market_info_by_symbol(
        symbol=symbol, exchange=exchange
    )
    return target_market["base"], target_market["quote"]


@router.post("/positions", response_model=ResponseSchema[ReadPositionResponse])
async def post_okx_positions(
    selected_okx_accounts: OKXPositionRequest,
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
    current_end_user: dict = Depends(get_current_end_user),
):
    """
    Sample request body:
    ```
    {
        "selected_okx_account_name": ["okx-data-01"]
    }
    ```

    """
    end_user_collection = chore_master_api_db.get_collection("end_user")
    account_info = end_user_collection.find(
        filter={"reference": current_end_user["reference"]}, projection={"_id": 0}
    )
    account_info = (await account_info.to_list(length=1))[0]
    if "okx_trade" not in account_info:
        return ResponseSchema(
            status=StatusEnum.SUCCESS, data=ReadAbcResponse(a="some string")
        )
    elif "account_map" not in account_info["okx_trade"]:
        return ResponseSchema(
            status=StatusEnum.SUCCESS, data=ReadAbcResponse(a="some string")
        )

    okx_account_info = account_info["okx_trade"]["account_map"]

    okx_accounts = defaultdict(dict)

    for selected_okx_account_name in selected_okx_accounts.selected_okx_account_names:
        if selected_okx_account_name in okx_account_info:
            okx_accounts[selected_okx_account_name] = okx_account_info[
                selected_okx_account_name
            ]
        else:
            logging.info(f"selected_okx_account_name: {selected_okx_account_name}")

    aggregated_positions = []

    for selected_account_name, okx_account in okx_accounts.items():
        exchange = ccxt.okx(
            {
                "apiKey": okx_account["api_key"],
                "secret": okx_account["passphrase"],
                "password": okx_account["password"],
                "enableRateLimit": True,
                # "sandbox": False if okx_account["env"] == "MAINNET" else True,
            }
        )
        # fetch all positions
        raw_positions = await exchange.fetch_positions()
        raw_balances = await exchange.fetch_balance({"type": "trading"})
        raw_balances_funding_account = await exchange.fetch_balance({"type": "funding"})
        finance_account = await exchange.privateGetFinanceSavingsBalance()

        # generate position by expression
        positions = [
            ReadPositionResponse.Position(
                symbol=position["symbol"],
                account_name=selected_account_name,
                max_leverage=position["leverage"],
                side=position["side"],
                token_amount=position["contracts"] * position["contractSize"],
                contract_amount=position["contracts"],
                liquidation_price=position["liquidationPrice"],
                entry_price=position["entryPrice"],
                mark_price=position["markPrice"],
                profit_and_loss=position["unrealizedPnl"] + position["realizedPnl"],
                realized_pnl=position["realizedPnl"],
                unrealized_pnl=position["unrealizedPnl"],
                percentage_to_liquidation=(
                    abs(
                        (position["liquidationPrice"] - position["markPrice"])
                        / position["markPrice"]
                    )
                    if position["liquidationPrice"] is not None
                    else None
                ),
                current_margin=position["initialMargin"],
                initial_margin=position["collateral"],
                maintenance_margin=position["maintenanceMargin"],
                margin_ratio=position["marginRatio"],
                instrument=await get_insturment_by_symbol(position["symbol"], exchange),
            )
            for position in raw_positions
        ]

        spot_positions = [
            ReadPositionResponse.Position(
                symbol=balance["ccy"],
                account_name=selected_account_name,
                max_leverage=1,
                side="long",
                token_amount=balance["eq"],
                contract_amount=None,
                liquidation_price=None,
                entry_price=None,
                mark_price=None,
                profit_and_loss=None,
                realized_pnl=None,
                unrealized_pnl=None,
                percentage_to_liquidation=None,
                current_margin=None,
                initial_margin=None,
                maintenance_margin=None,
                margin_ratio=(
                    float(Decimal(balance["mgnRatio"]))
                    if balance["mgnRatio"] != ""
                    else None
                ),
                instrument="spot",
            )
            for balance in raw_balances["info"]["data"][0]["details"]
        ]

        spot_positions_funding = [
            ReadPositionResponse.Position(
                symbol=balance["ccy"],
                account_name=selected_account_name,
                max_leverage=1,
                side="long",
                token_amount=balance["bal"],
                contract_amount=None,
                liquidation_price=None,
                entry_price=None,
                mark_price=None,
                profit_and_loss=None,
                realized_pnl=None,
                unrealized_pnl=None,
                percentage_to_liquidation=None,
                current_margin=None,
                initial_margin=None,
                maintenance_margin=None,
                margin_ratio=None,
                instrument="spot",
            )
            for balance in raw_balances_funding_account["info"]["data"]
        ]

        spot_positions_finance = [
            ReadPositionResponse.Position(
                symbol=balance["ccy"],
                account_name=selected_account_name,
                max_leverage=1,
                side="long",
                token_amount=balance["amt"],
                contract_amount=None,
                liquidation_price=None,
                entry_price=None,
                mark_price=None,
                profit_and_loss=None,
                realized_pnl=None,
                unrealized_pnl=None,
                percentage_to_liquidation=None,
                current_margin=None,
                initial_margin=None,
                maintenance_margin=None,
                margin_ratio=None,
                instrument="spot",
            )
            for balance in finance_account["data"]
        ]

        aggregated_positions.extend(positions)
        aggregated_positions.extend(spot_positions)
        aggregated_positions.extend(spot_positions_funding)
        aggregated_positions.extend(spot_positions_finance)

    return ResponseSchema(
        status=StatusEnum.SUCCESS,
        data=ReadPositionResponse(positions=aggregated_positions),
    )


def black_scholes(option_type, S, K, T, r, sigma):
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    if option_type == "call":
        price = S * (0.5 * (1.0 + erf(d1 / sqrt(2.0)))) - K * exp(-r * T) * (
            0.5 * (1.0 + erf(d2 / sqrt(2.0)))
        )
    else:
        price = K * exp(-r * T) * (0.5 * (1.0 + erf(-d2 / sqrt(2.0)))) - S * (
            0.5 * (1.0 + erf(-d1 / sqrt(2.0)))
        )

    return price


# Vega function (the derivative of option price with respect to volatility)
def vega(S, K, T, r, sigma):
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    return S * sqrt(T) * exp(-0.5 * d1**2) / sqrt(2 * pi)


# Newton-Raphson method to calculate implied volatility
def find_implied_volatility(
    option_type,
    option_price,
    S,
    K,
    T,
    r,
    initial_guess=0.2,
    tolerance=1e-6,
    max_iterations=100,
):
    sigma = initial_guess  # Initial guess for volatility
    for i in range(max_iterations):
        price = black_scholes(
            option_type, S, K, T, r, sigma
        )  # Current option price using guessed sigma
        v = vega(S, K, T, r, sigma)  # Current vega (sensitivity of price to volatility)

        price_diff = (
            price - option_price
        )  # Difference between market price and Black-Scholes price
        if (
            abs(price_diff) < tolerance
        ):  # If the difference is within the tolerance, we're done
            return sigma

        sigma -= price_diff / v  # Update sigma using Newton's method

    return sigma  # Return the result (may not have converged fully)


# Rho function (the derivative of option price with respect to risk-free interest rate)
def get_rho(option_type, S, K, T, r, sigma):
    d2 = (log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    if option_type == "call":
        return K * T * exp(-r * T) * (0.5 * (1.0 + erf(d2 / sqrt(2.0))))
    else:
        return -K * T * exp(-r * T) * (0.5 * (1.0 + erf(-d2 / sqrt(2.0))))


@router.post("/fxrisk", response_model=ResponseSchema[ReadPositionFxRiskResponse])
async def post_okx_fx_risk(
    selected_okx_accounts: OKXPositionRequest,
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
    current_end_user: dict = Depends(get_current_end_user),
):
    """
    Sample request body:
    ```
    {
        "selected_okx_account_names": ["okx-data-01"]
    }
    ```

    """
    positions_response = await post_okx_positions(
        selected_okx_accounts, chore_master_api_db, current_end_user
    )
    positions = positions_response.data.positions

    # Initialize positions_fx_risk dictionary
    positions_fx_risk = []

    exchange_rate_map = defaultdict(dict)
    # Iterate over each position and calculate the FX risk metrics
    for position in positions:
        exchange = ccxt.okx(
            {
                "enableRateLimit": True,
                # "sandbox": False if okx_account["env"] == "MAINNET" else True,
            }
        )
        # This is just a placeholder, replace with your actual logic to compute risk metrics
        if position.instrument != "spot":
            base_currency, quote_currency = await get_currencies_by_symbol(
                position.symbol, exchange
            )
        else:
            base_currency = position.symbol
            quote_currency = "USDT"

        if base_currency + "/" + quote_currency in exchange_rate_map:
            exchange_rate = exchange_rate_map[base_currency + "/" + quote_currency]
        else:

            # Get base currency to quote currency exchange rate
            query_symbol = (
                base_currency + "/" + quote_currency + "T"
                if quote_currency == "USD"
                else base_currency + "/" + quote_currency
            )
            exchange_rate = (
                (await exchange.fetch_ticker(query_symbol))["last"]
                if base_currency != quote_currency
                else 1
            )
            exchange_rate_map[query_symbol] = exchange_rate

        delta = 0.0
        gamma = 0.0
        vega = 0.0
        theta = 0.0

        if position.instrument == "spot":
            if base_currency == quote_currency:
                delta = 0.0
            else:
                delta = position.token_amount * (
                    +0.01 * exchange_rate
                    if position.side == "long"
                    else -0.01 * exchange_rate
                )
            gamma = 0.0
            vega = 0.0
            theta = 0.0

        elif position.instrument == "future":
            market_info = await get_okx_market_info_by_symbol(position.symbol, exchange)
            maturity_time = datetime.strptime(
                market_info["expiryDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            current_time = datetime.utcnow()
            days_to_maturity = float((maturity_time - current_time).days)
            if days_to_maturity < 1:
                seconds_to_maturity = (maturity_time - current_time).seconds
                days_to_maturity = seconds_to_maturity / (24 * 60 * 60)
            time_to_maturity = days_to_maturity / 365
            time_to_maturity_tomorrow = max((days_to_maturity - 1), 0.0) / 365
            if days_to_maturity <= 1.0:
                theta = 0.0
            else:
                # get the spot price from the order book
                spot_symbol = base_currency + "/" + quote_currency
                spot_price = await exchange.fetch_ticker(spot_symbol)
                implied_term_rate = (
                    (position.mark_price - spot_price["last"])
                    / spot_price["last"]
                    / time_to_maturity
                )
                term_price_today = spot_price["last"] * (
                    1 + implied_term_rate * time_to_maturity
                )
                theoretical_term_price_in_tomorrow = spot_price["last"] * (
                    1 + implied_term_rate * time_to_maturity_tomorrow
                )
                theta = (
                    (theoretical_term_price_in_tomorrow - term_price_today)
                    * position.token_amount
                    * (+1 if position.side == "long" else -1)
                )
            delta = position.token_amount * (
                +0.01 * exchange_rate
                if position.side == "long"
                else -0.01 * exchange_rate
            )
            gamma = 0.0
            vega = 0.0

        elif position.instrument == "option":
            continue
            market_info = await get_okx_market_info_by_symbol(position.symbol, exchange)
            spot_symbol = base_currency + "/" + quote_currency
            spot_price = await exchange.fetch_ticker(spot_symbol)
            option_type = market_info["info"]["optionType"]
            maturity_time = market_info["info"]["settlementTime"]
            strike_price = market_info["info"]["strike"]
            # Days to maturity
            current_time = datetime.now().timestamp()
            days_to_maturity = (maturity_time - current_time) / (24 * 60 * 60)
            time_to_maturity = days_to_maturity / 365
            time_to_maturity_tomorrow = (days_to_maturity - 1) / 365

            # Implied volatility
            option_ticker = await exchange.fetch_ticker(position.symbol)
            option_price = option_ticker["last"]
            implied_term_rate = (1 / spot_price["last"]) ** (1 / days_to_maturity) - 1
            sigma = find_implied_volatility(
                option_type,
                option_price,
                spot_price["last"],
                strike_price,
                time_to_maturity,
                implied_term_rate,
                max_iterations=1000,
            )

            # Black-Scholes parameters
            d1 = (
                log(spot_price / strike_price)
                + (implied_term_rate + 0.5 * sigma**2) * time_to_maturity
            ) / (sigma * sqrt(time_to_maturity))
            d2 = d1 - sigma * sqrt(time_to_maturity)

            # CDF and PDF from numpy equivalent for normal distribution
            norm_cdf = lambda x: (1.0 + erf(x / sqrt(2.0))) / 2.0
            norm_pdf = lambda x: exp(-0.5 * x**2) / sqrt(2 * pi)

            # Calculate Greeks
            delta = norm_cdf(d1) if option_type == "call" else norm_cdf(d1) - 1
            gamma = norm_pdf(d1) / (spot_price * sigma * sqrt(time_to_maturity))
            vega = spot_price * norm_pdf(d1) * sqrt(time_to_maturity)
            theta = (
                -spot_price * norm_pdf(d1) * sigma / (2 * sqrt(time_to_maturity))
            ) - (
                implied_term_rate
                * strike_price
                * exp(-implied_term_rate * time_to_maturity)
                * norm_cdf(d2 if option_type == "call" else -d2)
            )

        elif position.instrument == "perpetual":
            delta = position.token_amount * (
                +0.01 * exchange_rate
                if position.side == "long"
                else -0.01 * exchange_rate
            )
            gamma = 0.0
            vega = 0.0
            theta = 0.0
        else:
            logging.info(f"symbol: {position.symbol}, greeks do not calculate")

        fx_risk = ReadPositionFxRiskResponse.PositionFxRisk(
            symbol=position.symbol,
            instrument=position.instrument,
            base_currency=base_currency,
            quote_currency=quote_currency,
            account_name=position.account_name,
            side=position.side,
            token_amount=position.token_amount,
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta,
        )

        # Add to the positions_fx_risk dictionary with the symbol as the key
        positions_fx_risk.append(fx_risk)

    # Return the response with the calculated positions_fx_risk
    return ResponseSchema(
        status=StatusEnum.SUCCESS,
        data=ReadPositionFxRiskResponse(positions_fx_risk=positions_fx_risk),
    )


@router.post("/irrisk", response_model=ResponseSchema[ReadPositionIrRiskResponse])
async def post_okx_ir_risk(
    selected_okx_accounts: OKXPositionRequest,
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
    current_end_user: dict = Depends(get_current_end_user),
):
    """
    Sample request body:
    ```
    {
        "selected_okx_account_names": ["okx-data-01"]
    }
    ```

    """
    positions_response = await post_okx_positions(
        selected_okx_accounts, chore_master_api_db, current_end_user
    )
    positions = positions_response.data.positions

    # Initialize positions_fx_risk dictionary
    positions_ir_risk = []
    # Iterate over each position and calculate the FX risk metrics
    for position in positions:
        exchange = ccxt.okx(
            {
                "enableRateLimit": True,
                # "sandbox": False if okx_account["env"] == "MAINNET" else True,
            }
        )
        if position.instrument != "spot":
            base_currency, quote_currency = await get_currencies_by_symbol(
                position.symbol, exchange
            )
        else:
            base_currency = position.symbol
            quote_currency = "USDT"

        # DV01 and Rho change interest rate by 1 percentage point
        change_in_interest_rate = 0.01

        dvo1 = 0.0
        rho = 0.0

        if position.instrument == "spot":
            dvo1 = 0.0
            rho = 0.0

        elif position.instrument == "future":
            market_info = await get_okx_market_info_by_symbol(position.symbol, exchange)
            maturity_time = datetime.strptime(
                market_info["expiryDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            current_time = datetime.utcnow()
            days_to_maturity = float((maturity_time - current_time).days)
            if days_to_maturity < 1:
                seconds_to_maturity = (maturity_time - current_time).seconds
                days_to_maturity = seconds_to_maturity / (24 * 60 * 60)
            time_to_maturity = days_to_maturity / 365
            if days_to_maturity <= 1.0:
                dvo1 = 0.0
            else:
                # get the spot price from the order book
                spot_symbol = base_currency + "/" + quote_currency
                spot_price = await exchange.fetch_ticker(spot_symbol)
                implied_term_rate = (
                    (position.mark_price - spot_price["last"])
                    / spot_price["last"]
                    / time_to_maturity
                )
                term_price_today = spot_price["last"] * (
                    1 + implied_term_rate * time_to_maturity
                )
                term_price_after_change_in_interest_rate = spot_price["last"] * (
                    1 + (implied_term_rate + change_in_interest_rate) * time_to_maturity
                )
                dvo1 = (
                    (term_price_after_change_in_interest_rate - term_price_today)
                    * position.token_amount
                    * (+1 if position.side == "long" else -1)
                )
            rho = 0.0

        elif position.instrument == "option":
            market_info = await get_okx_market_info_by_symbol(position.symbol, exchange)
            if quote_currency == "USD":
                spot_symbol = base_currency + "/" + quote_currency + "T"
            spot_price = await exchange.fetch_ticker(spot_symbol)
            option_type = "put" if market_info["id"][-1:] == "P" else "call"
            maturity_time = datetime.strptime(
                market_info["expiryDatetime"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            strike_price = float(Decimal(market_info["strike"]))
            # Days to maturity
            current_time = datetime.now()
            days_to_maturity = float((maturity_time - current_time).days)
            if days_to_maturity < 1:
                seconds_to_maturity = (maturity_time - current_time).seconds
                days_to_maturity = seconds_to_maturity / (24 * 60 * 60)
            time_to_maturity = days_to_maturity / 365

            # Implied volatility
            option_ticker = await exchange.fetch_ticker(position.symbol)
            option_price = option_ticker["last"]
            implied_term_rate = 0  # TODO: build yield curve
            sigma = 0.1  # TODO: find_implied_volatility

            rho = 0.1
            dvo1 = 0.0
        elif position.instrument == "perpetual":
            dvo1 = 0.0
            rho = 0.0
        else:
            logging.info(f"symbol: {position.symbol}, greeks do not calculate")

        # generate position by expression
        ir_risk = ReadPositionIrRiskResponse.PositionIrRisk(
            symbol=position.symbol,
            instrument=position.instrument,
            base_currency=base_currency,
            quote_currency=quote_currency,
            account_name=position.account_name,
            side=position.side,
            token_amount=position.token_amount,
            dv01=dvo1,
            rho=rho,
        )
        positions_ir_risk.append(ir_risk)

    return ResponseSchema(
        status=StatusEnum.SUCCESS,
        data=ReadPositionIrRiskResponse(positions_ir_risk=positions_ir_risk),
    )
