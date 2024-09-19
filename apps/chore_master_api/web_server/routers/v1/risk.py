import logging
from collections import defaultdict

import ccxt.async_support as ccxt
from fastapi import APIRouter, Body, Depends
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
        max_leverage: float
        side: str
        token_amount: float
        contract_amount: float
        liquidation_price: float
        entry_price: float
        mark_price: float
        profit_and_loss: float
        realized_pnl: float
        unrealized_pnl: float
        percentage_to_liquidation: float
        current_margin: float
        initial_margin: float
        maintenance_margin: float
        margin_ratio: float

    positions: dict[str, Position]


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

    positions_fx_risk: dict[str, PositionFxRisk]


class ReadPositionIrRiskResponse(BaseModel):
    class PositionIrRisk(BaseModel):
        symbol: str
        base_currency: str
        quote_currency: str
        account_name: str
        side: str
        token_amount: float
        dv01: float
        rho: float

    positions_fx_risk: dict[str, PositionIrRisk]


class ReadPositionAlertResponse(BaseModel):
    class PositionRiskAlert(BaseModel):
        aggregated_dv01: float
        aggregated_gamma: float
        aggregated_theta: float
        aggregated_vega: float
        aggregated_rho: float
        aggregated_delta: float
        aggregated_profit_and_loss: float

    positions_fx_risk: dict[str, PositionRiskAlert]


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
        "selected_okx_accounts": ["okx-data-01"]
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
        # generate position by expression
        positions = {
            position["symbol"]: ReadPositionResponse.Position(
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
                ),
                current_margin=position["initialMargin"],
                initial_margin=position["collateral"],
                maintenance_margin=position["maintenanceMargin"],
                margin_ratio=position["marginRatio"],
                instrument=await get_insturment_by_symbol(position["symbol"], exchange),
            )
            for position in raw_positions
        }

    return ResponseSchema(
        status=StatusEnum.SUCCESS, data=ReadPositionResponse(positions=positions)
    )


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
        "selected_okx_accounts": ["okx-data-01"]
    }
    ```

    """
    positions_response = await post_okx_positions(
        selected_okx_accounts, chore_master_api_db, current_end_user
    )
    positions = positions_response.data.positions

    # Initialize positions_fx_risk dictionary
    positions_fx_risk = defaultdict(dict)
    # Iterate over each position and calculate the FX risk metrics
    for symbol, position in positions.items():
        exchange = ccxt.okx(
            {
                "enableRateLimit": True,
                # "sandbox": False if okx_account["env"] == "MAINNET" else True,
            }
        )
        # This is just a placeholder, replace with your actual logic to compute risk metrics
        base_currency, quote_currency = await get_currencies_by_symbol(symbol, exchange)

        delta = 0.0
        gamma = 0.0
        vega = 0.0
        theta = 0.0

        if position.instrument == "spot":
            delta = position.token_amount
            gamma = 0.0
            vega = 0.0
            theta = 0.0

        elif position.instrument == "future":
            delta = position.token_amount
            gamma = 0.0
            vega = 0.0
            theta = 0.0

        elif position.instrument == "option":
            # TODO: Implement the calculation of greeks for options
            delta = position.token_amount
            gamma = 0.0
            vega = 0.0
            theta = 0.0

        elif position.instrument == "perpetual":
            delta = position.token_amount
            gamma = 0.0
            vega = 0.0
            theta = 0.0
        else:
            logging.info(f"symbol: {symbol}, greeks do not calculate")

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
        positions_fx_risk[symbol] = fx_risk

    # Return the response with the calculated positions_fx_risk
    return ResponseSchema(
        status=StatusEnum.SUCCESS,
        data=ReadPositionFxRiskResponse(positions_fx_risk=positions_fx_risk),
    )


@router.post("/irrisk", response_model=ResponseSchema[ReadPositionResponse])
async def post_okx_ir_risk(
    selected_okx_accounts: OKXPositionRequest,
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
    current_end_user: dict = Depends(get_current_end_user),
):
    """
    Sample request body:
    ```
    {
        "selected_okx_accounts": ["okx-data-01"]
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
        # generate position by expression
        positions = {
            position["symbol"]: ReadPositionResponse.Position(
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
                ),
                current_margin=position["initialMargin"],
                initial_margin=position["collateral"],
                maintenance_margin=position["maintenanceMargin"],
                margin_ratio=position["marginRatio"],
            )
            for position in raw_positions
        }

    return ResponseSchema(
        status=StatusEnum.SUCCESS, data=ReadPositionResponse(positions=positions)
    )
