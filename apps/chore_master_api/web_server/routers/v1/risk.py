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


@router.get("/abc", response_model=ResponseSchema[ReadAbcResponse])
async def get_some_entities():
    return ResponseSchema(
        status=StatusEnum.SUCCESS, data=ReadAbcResponse(a="some string")
    )


# Define a Pydantic model for the request
class OKXPositionRequest(BaseModel):
    selected_okx_account_names: list[str]


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
            )
            for position in raw_positions
        }

    return ResponseSchema(
        status=StatusEnum.SUCCESS, data=ReadPositionResponse(positions=positions)
    )
