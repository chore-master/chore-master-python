from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from apps.chore_master_api.models.base import Entity


class Account(Entity):
    name: str


class Asset(Entity):
    symbol: str


class NetValue(Entity):
    account_reference: UUID
    amount: Decimal
    settlement_asset_reference: UUID
    settled_time: datetime


class Bill(Entity):
    account_reference: UUID
    business_type: str
    accounting_type: str
    amount_change: Decimal
    asset_reference: UUID
    order_reference: Optional[str] = None
    billed_time: datetime
