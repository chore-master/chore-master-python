from typing import Type

from apps.chore_master_api.models.some_module import SomeEntity
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class SomeEntityRepository(BaseSQLAlchemyRepository[SomeEntity]):
    @property
    def entity_class(self) -> Type[SomeEntity]:
        return SomeEntity
