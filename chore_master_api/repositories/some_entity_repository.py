from typing import Type

from chore_master_api.models.some_entity import SomeEntity
from chore_master_api.repositories.base_repository import SheetRepository


class SomeEntityRepository(SheetRepository[SomeEntity]):
    @property
    def _model(self) -> Type[SomeEntity]:
        return SomeEntity
