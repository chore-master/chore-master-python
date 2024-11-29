from typing import Type

from apps.chore_master_api.end_user_space.models.financial_management import (
    Account,
    Asset,
    Bill,
    NetValue,
)
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class AccountRepository(BaseSQLAlchemyRepository[Account]):
    @property
    def entity_class(self) -> Type[Account]:
        return Account


class AssetRepository(BaseSQLAlchemyRepository[Asset]):
    @property
    def entity_class(self) -> Type[Asset]:
        return Asset


class NetValueRepository(BaseSQLAlchemyRepository[NetValue]):
    @property
    def entity_class(self) -> Type[NetValue]:
        return NetValue


class BillRepository(BaseSQLAlchemyRepository[Bill]):
    @property
    def entity_class(self) -> Type[Bill]:
        return Bill
