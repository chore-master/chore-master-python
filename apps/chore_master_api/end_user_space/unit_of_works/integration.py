from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories import integration
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class IntegrationSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> IntegrationSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.operator_repository = integration.OperatorRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.operator_repository = None
        await super().__aexit__(*args)
