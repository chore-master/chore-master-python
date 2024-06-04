from __future__ import annotations

import abc

from googleapiclient.discovery import Resource

from chore_master_api.repositories.some_entity_repository import SomeEntityRepository


class AbstractUnitOfWork(abc.ABC):
    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    async def __aexit__(self, *args):
        await self._rollback()

    async def commit(self):
        await self._commit()

    async def rollback(self):
        await self._rollback()

    @abc.abstractmethod
    async def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def _rollback(self):
        raise NotImplementedError


class SpreadsheetUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        sheets_service: Resource,
        some_entity_spreadsheet_id: str,
        some_entity_sheet_id: str,
    ):
        self._sheets_service = sheets_service
        self._some_entity_spreadsheet_id = some_entity_spreadsheet_id
        self._some_entity_sheet_id = some_entity_sheet_id

    async def __aenter__(self) -> SpreadsheetUnitOfWork:
        await super().__aenter__()
        self.some_entity_repository = SomeEntityRepository(
            self._sheets_service,
            self._some_entity_spreadsheet_id,
            self._some_entity_sheet_id,
        )
        return self

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        self.some_entity_repository = None

    async def _commit(self):
        pass

    async def _rollback(self):
        pass
