from __future__ import annotations

import abc

from googleapiclient.discovery import Resource


class AbstractUnitOfWork(abc.ABC):
    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    async def commit(self):
        await self._commit()

    @abc.abstractmethod
    async def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError


class SpreadsheetUnitOfWork(AbstractUnitOfWork):
    def __init__(self, sheets_service: Resource):
        self._sheets_service = sheets_service

    async def __aenter__(self) -> SpreadsheetUnitOfWork:
        await super().__aenter__()
        self.some_entity_repository = SomeEntityRepository(self._sheets_service)
        return self

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        self.some_entity_repository = None

    async def _commit(self):
        pass

    async def rollback(self):
        pass
