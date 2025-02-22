from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import ConfigDict

from apps.chore_master_api.end_user_space.models.base import Entity


class Account(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class EcosystemTypeEnum(Enum):
        TRAD_FI = "TRAD_FI"

    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: EcosystemTypeEnum


class Asset(Entity):
    name: str
    symbol: str
    is_settleable: bool


class BalanceSheet(Entity):
    balanced_time: datetime


class BalanceEntry(Entity):
    model_config = ConfigDict(use_enum_values=True)

    class TypeEnum(Enum):
        ASSET = "ASSET"
        LIABILITY = "LIABILITY"

    balance_sheet_reference: str
    account_reference: str
    asset_reference: str
    entry_type: TypeEnum
    amount: Decimal
