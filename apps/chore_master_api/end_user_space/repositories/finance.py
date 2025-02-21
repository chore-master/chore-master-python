from typing import Type

from apps.chore_master_api.end_user_space.models.finance import (
    Account,
    Asset,
    BalanceEntry,
    BalanceSheet,
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


class BalanceSheetRepository(BaseSQLAlchemyRepository[BalanceSheet]):
    @property
    def entity_class(self) -> Type[BalanceSheet]:
        return BalanceSheet


class BalanceEntryRepository(BaseSQLAlchemyRepository[BalanceEntry]):
    @property
    def entity_class(self) -> Type[BalanceEntry]:
        return BalanceEntry
