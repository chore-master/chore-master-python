from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories.trace import QuotaRepository
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class TraceSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> TraceSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.quota_repository = QuotaRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.quota_repository = None
        await super().__aexit__(*args)
