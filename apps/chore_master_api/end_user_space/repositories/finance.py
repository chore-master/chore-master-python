from typing import Type

from apps.chore_master_api.end_user_space.models.finance import (
    Account,
    Asset,
    BalanceEntry,
    BalanceSheet,
    Portfolio,
    Price,
    Transaction,
    Transfer,
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


class PriceRepository(BaseSQLAlchemyRepository[Price]):
    @property
    def entity_class(self) -> Type[Price]:
        return Price


class BalanceSheetRepository(BaseSQLAlchemyRepository[BalanceSheet]):
    @property
    def entity_class(self) -> Type[BalanceSheet]:
        return BalanceSheet


class BalanceEntryRepository(BaseSQLAlchemyRepository[BalanceEntry]):
    @property
    def entity_class(self) -> Type[BalanceEntry]:
        return BalanceEntry


class PortfolioRepository(BaseSQLAlchemyRepository[Portfolio]):
    @property
    def entity_class(self) -> Type[Portfolio]:
        return Portfolio


class TransactionRepository(BaseSQLAlchemyRepository[Transaction]):
    @property
    def entity_class(self) -> Type[Transaction]:
        return Transaction


class TransferRepository(BaseSQLAlchemyRepository[Transfer]):
    @property
    def entity_class(self) -> Type[Transfer]:
        return Transfer
