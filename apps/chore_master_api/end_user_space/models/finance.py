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


class Account(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class EcosystemTypeEnum(Enum):
        TRAD_FI = "TRAD_FI"

    user_reference: str
    settlement_asset_reference: str
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: EcosystemTypeEnum


class BalanceSheet(Entity):
    user_reference: str
    balanced_time: datetime


class BalanceEntry(Entity):
    balance_sheet_reference: str
    account_reference: str
    amount: int


class Instrument(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class InstrumentTypeEnum(Enum):
        STOCK = "STOCK"
        FOREX = "FOREX"
        DERIVATIVE = "DERIVATIVE"
        LENDING = "LENDING"

    user_reference: str
    name: str
    quantity_decimals: int
    px_decimals: int
    instrument_type: InstrumentTypeEnum
    base_asset_reference: Optional[str] = None
    quote_asset_reference: Optional[str] = None
    settlement_asset_reference: Optional[str] = None
    underlying_asset_reference: Optional[str] = None
    staking_asset_reference: Optional[str] = None
    yielding_asset_reference: Optional[str] = None


class Portfolio(Entity):
    user_reference: str
    name: str
    description: Optional[str]


class LedgerEntry(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class SourceTypeEnum(Enum):
        MANUAL = "MANUAL"
        MANAGED = "MANAGED"

    class EntryTypeEnum(Enum):
        TRADE_BUY = "TRADE_BUY"
        TRADE_SELL = "TRADE_SELL"
        STAKE = "STAKE"
        UNSTAKE = "UNSTAKE"
        CASH_DIVIDEND = "CASH_DIVIDEND"
        STOCK_DIVIDEND = "STOCK_DIVIDEND"
        REWARD = "REWARD"
        FUNDING_FEE = "FUNDING_FEE"
        INTEREST = "INTEREST"

    portfolio_reference: str
    source_type: SourceTypeEnum
    entry_time: datetime
    entry_type: EntryTypeEnum
    settlement_amount_change: int
    settlement_asset_reference: str
    instrument_reference: Optional[str] = None
    quantity_change: Optional[int] = None
    fill_px: Optional[int] = None
    remark: Optional[str] = None


class FeeEntry(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class FeeTypeEnum(Enum):
        TRADE = "TRADE"
        TAX = "TAX"
        GAS = "GAS"

    ledger_entry_reference: str
    fee_type: FeeTypeEnum
    amount_change: int
    asset_reference: str
