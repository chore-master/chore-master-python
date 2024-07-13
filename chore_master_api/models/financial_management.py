from datetime import datetime
from decimal import Decimal
from uuid import UUID

from chore_master_api.models.base import Entity


class Account(Entity):
    name: str


class Asset(Entity):
    symbol: str


class NetValue(Entity):
    account_reference: UUID
    amount: Decimal
    settlement_asset_reference: str
    settled_time: datetime
