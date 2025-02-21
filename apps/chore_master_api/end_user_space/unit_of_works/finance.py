from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories.finance import AccountRepository
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class FinanceSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> FinanceSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.account_repository = AccountRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.account_repository = None
        await super().__aexit__(*args)
