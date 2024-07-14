from datetime import datetime
from decimal import Decimal
from typing import Optional

from apps.chore_master_api.models.base import Entity


class SomeEntity(Entity):
    a: bool
    b: int
    c: float
    d: Decimal
    e: str
    f: datetime
    g: str
    h: Optional[int] = None
    i: Optional[dict] = None
