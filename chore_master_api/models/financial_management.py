from datetime import datetime
from decimal import Decimal
from uuid import UUID

from chore_master_api.models.base import Entity


class Account(Entity):
    name: str


class Passbook(Entity):
    account_reference: UUID
    balance_amount: Decimal
    balance_symbol: str
    created_time: datetime
