from typing import Type

from apps.chore_master_api.end_user_space.models.integration import Operator
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class OperatorRepository(BaseSQLAlchemyRepository[Operator]):
    @property
    def entity_class(self) -> Type[Operator]:
        return Operator
