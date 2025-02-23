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
