from typing import Type

from apps.chore_master_api.end_user_space.models.finance import Account
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class AccountRepository(BaseSQLAlchemyRepository[Account]):
    @property
    def entity_class(self) -> Type[Account]:
        return Account
