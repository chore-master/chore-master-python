from typing import Type

from apps.chore_master_api.end_user_space.models.integration import Resource
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class ResourceRepository(BaseSQLAlchemyRepository[Resource]):
    @property
    def entity_class(self) -> Type[Resource]:
        return Resource
