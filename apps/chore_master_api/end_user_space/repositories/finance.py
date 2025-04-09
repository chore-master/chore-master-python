from typing import Type

from apps.chore_master_api.end_user_space.models.finance import (  # Instrument,; LedgerEntry,
    Account,
    Asset,
    BalanceEntry,
    BalanceSheet,
    Portfolio,
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


class BalanceSheetRepository(BaseSQLAlchemyRepository[BalanceSheet]):
    @property
    def entity_class(self) -> Type[BalanceSheet]:
        return BalanceSheet


class BalanceEntryRepository(BaseSQLAlchemyRepository[BalanceEntry]):
    @property
    def entity_class(self) -> Type[BalanceEntry]:
        return BalanceEntry


# class InstrumentRepository(BaseSQLAlchemyRepository[Instrument]):
#     @property
#     def entity_class(self) -> Type[Instrument]:
#         return Instrument


class PortfolioRepository(BaseSQLAlchemyRepository[Portfolio]):
    @property
    def entity_class(self) -> Type[Portfolio]:
        return Portfolio


# class LedgerEntryRepository(BaseSQLAlchemyRepository[LedgerEntry]):
#     @property
#     def entity_class(self) -> Type[LedgerEntry]:
#         return LedgerEntry


class TransactionRepository(BaseSQLAlchemyRepository[Transaction]):
    @property
    def entity_class(self) -> Type[Transaction]:
        return Transaction


class TransferRepository(BaseSQLAlchemyRepository[Transfer]):
    @property
    def entity_class(self) -> Type[Transfer]:
        return Transfer
