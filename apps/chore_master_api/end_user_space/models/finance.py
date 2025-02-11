from datetime import datetime
from decimal import Decimal
from enum import Enum

from apps.chore_master_api.end_user_space.models.base import Entity


class Account(Entity):  # `Wallet` in defi
    class SystemTypeEnum(Enum):
        TRAD_FI = "TRAD_FI"
        DEFI = "DEFI"
        CEFI = "CEFI"

    system_type: SystemTypeEnum
    name: str


class Instrument(Entity):  # `Token` in defi
    class TypeEnum(Enum):
        CURRENCY = "CURRENCY"
        FX = "FX"
        STOCK = "STOCK"
        BOND = "BOND"
        COMMODITY = "COMMODITY"

    symbol: str
    type: TypeEnum


class BalanceEntry(Entity):
    class TypeEnum(Enum):
        ASSET = "ASSET"
        LIABILITY = "LIABILITY"

    account_reference: str
    instrument_reference: str
    entry_type: TypeEnum
    amount: Decimal
    price: Decimal
    currency_instrument_reference: str
    log_time: datetime


"""
需求：
1. Asset 和 Liability 要能區隔，不能只依靠 amount 的正負
2. 要能設定多種結算貨幣
2. 價值要能以多種貨幣結算
"""
