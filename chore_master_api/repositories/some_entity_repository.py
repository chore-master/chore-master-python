from typing import Type

from chore_master_api.models.some_entity import SomeEntity
from chore_master_api.repositories.base_repository import BaseSheetRepository


class SomeEntityRepository(BaseSheetRepository[SomeEntity]):
    @property
    def entity_class(self) -> Type[SomeEntity]:
        return SomeEntity

    @property
    def sheet_title(self) -> str:
        return "some_entity"
