from __future__ import annotations

import abc

from chore_master_api.repositories.some_entity_repository import SomeEntityRepository
from modules.google_service.google_service import GoogleService


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
        google_service: GoogleService,
        spreadsheet_id: str,
    ):
        self._google_service = google_service
        self._spreadsheet_id = spreadsheet_id
        self._batch_update_spreadsheet_session = (
            self._google_service.batch_update_spreadsheet_session(self._spreadsheet_id)
        )

    async def __aenter__(self) -> SpreadsheetUnitOfWork:
        await super().__aenter__()
        batch_update_requests = self._batch_update_spreadsheet_session.__enter__()
        self.some_entity_repository = SomeEntityRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        return self

    async def __aexit__(self, *args):
        self.some_entity_repository = None
        await super().__aexit__(*args)

    async def _commit(self):
        self._batch_update_spreadsheet_session.__exit__(None, None, None)

    async def _rollback(self):
        pass
