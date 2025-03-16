from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from modules.database.relational_database import RelationalDatabase
from modules.unit_of_works.base_unit_of_work import BaseUnitOfWork


class BaseSQLAlchemyUnitOfWork(BaseUnitOfWork):
    def __init__(self, relational_database: RelationalDatabase):
        self._relational_database = relational_database

    async def __aenter__(self) -> BaseSQLAlchemyUnitOfWork:
        async_session = self._relational_database.get_async_session()
        async with async_session() as session:
            self.session: AsyncSession = session
            await super().__aenter__()
            return self

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await asyncio.shield(self.session.close())

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()
