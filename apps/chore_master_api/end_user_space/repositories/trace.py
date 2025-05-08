from typing import Type

from apps.chore_master_api.end_user_space.models.trace import Quota
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class QuotaRepository(BaseSQLAlchemyRepository[Quota]):
    @property
    def entity_class(self) -> Type[Quota]:
        return Quota
