from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories.finance import (  # InstrumentRepository,; LedgerEntryRepository,
    AccountRepository,
    AssetRepository,
    BalanceEntryRepository,
    BalanceSheetRepository,
    PortfolioRepository,
    TransactionRepository,
    TransferRepository,
)
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class FinanceSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> FinanceSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.account_repository = AccountRepository(self.session)
        self.asset_repository = AssetRepository(self.session)
        self.balance_sheet_repository = BalanceSheetRepository(self.session)
        self.balance_entry_repository = BalanceEntryRepository(self.session)
        # self.instrument_repository = InstrumentRepository(self.session)
        self.portfolio_repository = PortfolioRepository(self.session)
        # self.ledger_entry_repository = LedgerEntryRepository(self.session)
        self.transaction_repository = TransactionRepository(self.session)
        self.transfer_repository = TransferRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.transfer_repository = None
        self.transaction_repository = None
        # self.ledger_entry_repository = None
        self.portfolio_repository = None
        # self.instrument_repository = None
        self.balance_entry_repository = None
        self.balance_sheet_repository = None
        self.asset_repository = None
        self.account_repository = None
        await super().__aexit__(*args)
