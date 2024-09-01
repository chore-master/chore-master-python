from __future__ import annotations

from apps.chore_master_api.repositories.some_module import SomeEntityRepository
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class SomeModuleSQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> SomeModuleSQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.some_entity_repository = SomeEntityRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.some_entity_repository = None
        await super().__aexit__(*args)
