from typing import Optional

from chore_master_api.models.base import Entity


class SomeEntity(Entity):
    x: Optional[int]
    y: bool
