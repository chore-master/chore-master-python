from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import ConfigDict

from apps.chore_master_api.end_user_space.models.base import Entity


class Asset(Entity):
    name: str
    symbol: str
    decimals: int
    is_settleable: bool


class Account(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class EcosystemTypeEnum(Enum):
        TRAD_FI = "TRAD_FI"

    settlement_asset_reference: str
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: EcosystemTypeEnum


class BalanceSheet(Entity):
    balanced_time: datetime


class BalanceEntry(Entity):
    balance_sheet_reference: str
    account_reference: str
    amount: int


class Instrument(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class InstrumentTypeEnum(Enum):
        EQUITY = "EQUITY"
        FX = "FX"
        EARNING = "EARNING"

    name: str
    quantity_decimals: int
    price_decimals: int
    instrument_type: InstrumentTypeEnum
    base_asset_reference: Optional[str]
    quote_asset_reference: Optional[str]
    settlement_asset_reference: Optional[str]
    underlying_asset_reference: Optional[str]
    staking_asset_reference: Optional[str]
    yielding_asset_reference: Optional[str]


class Portfolio(Entity):
    name: str
    description: Optional[str]


class LedgerEntry(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class EntryTypeEnum(Enum):
        BUY = "BUY"
        SELL = "SELL"
        STAKE = "STAKE"
        UNSTAKE = "UNSTAKE"
        CASH_DIVIDEND = "CASH_DIVIDEND"
        STOCK_DIVIDEND = "STOCK_DIVIDEND"
        FUNDING_FEE = "FUNDING_FEE"
        INTEREST = "INTEREST"

    class SourceTypeEnum(Enum):
        MANUAL = "MANUAL"
        MANAGED = "MANAGED"

    portfolio_reference: str
    instrument_reference: str
    entry_type: EntryTypeEnum
    source_type: SourceTypeEnum
    quantity: int
    price: int
    entry_time: datetime


class FeeEntry(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class FeeTypeEnum(Enum):
        TRADE = "TRADE"
        TAX = "TAX"
        GAS = "GAS"

    ledger_entry_reference: str
    fee_type: FeeTypeEnum
    amount: int
    asset_reference: str
