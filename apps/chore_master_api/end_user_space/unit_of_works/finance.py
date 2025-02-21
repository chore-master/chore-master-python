from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories.finance import (
    AccountRepository,
    AssetRepository,
    BalanceEntryRepository,
    BalanceSheetRepository,
)
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class FinanceSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> FinanceSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.account_repository = AccountRepository(self.session)
        self.asset_repository = AssetRepository(self.session)
        self.balance_sheet_repository = BalanceSheetRepository(self.session)
        self.balance_entry_repository = BalanceEntryRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.balance_entry_repository = None
        self.balance_sheet_repository = None
        self.asset_repository = None
        self.account_repository = None
        await super().__aexit__(*args)
