from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import ConfigDict

from apps.chore_master_api.end_user_space.models.base import Entity


class Asset(Entity):
    user_reference: str
    name: str
    symbol: str
    decimals: int
    is_settleable: bool


class Price(Entity):
    user_reference: str
    base_asset_reference: str
    quote_asset_reference: str
    value: str
    confirmed_time: datetime


class Account(Entity):
    user_reference: str
    settlement_asset_reference: str
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]


class BalanceSheet(Entity):
    user_reference: str
    balanced_time: datetime


class BalanceEntry(Entity):
    balance_sheet_reference: str
    account_reference: str
    amount: str


class Portfolio(Entity):
    user_reference: str
    name: str
    settlement_asset_reference: str
    description: Optional[str]


class Transaction(Entity):
    portfolio_reference: str
    transacted_time: datetime
    chain_id: Optional[str]
    tx_hash: Optional[str]
    remark: Optional[str]


class Transfer(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class FlowTypeEnum(Enum):
        COST = "COST"
        EXPENSE = "EXPENSE"
        REVENUE = "REVENUE"
        UPDATE_POSITION = "UPDATE_POSITION"

    transaction_reference: str
    flow_type: FlowTypeEnum
    asset_amount_change: str
    asset_reference: str
    settlement_asset_amount_change: Optional[str]
    remark: Optional[str]
