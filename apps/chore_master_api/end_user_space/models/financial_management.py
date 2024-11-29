from datetime import datetime
from decimal import Decimal
from typing import Optional

from apps.chore_master_api.end_user_space.models.base import Entity


class Account(Entity):
    name: str


class Asset(Entity):
    symbol: str


class NetValue(Entity):
    account_reference: str
    amount: Decimal
    settlement_asset_reference: str
    settled_time: datetime


class Bill(Entity):
    account_reference: str
    business_type: str
    accounting_type: str
    amount_change: Decimal
    asset_reference: str
    order_reference: Optional[str] = None
    billed_time: datetime
