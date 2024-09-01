from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories.financial_management import (
    AccountRepository,
    AssetRepository,
    BillRepository,
    NetValueRepository,
)
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class FinancialManagementSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> FinancialManagementSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.account_repository = AccountRepository(self.session)
        self.asset_repository = AssetRepository(self.session)
        self.net_value_repository = NetValueRepository(self.session)
        self.bill_repository = BillRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.bill_repository = None
        self.net_value_repository = None
        self.asset_repository = None
        self.account_repository = None
        await super().__aexit__(*args)
