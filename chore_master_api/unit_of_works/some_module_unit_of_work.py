from __future__ import annotations

from chore_master_api.repositories.some_module.some_entity_repository import (
    SomeEntityRepository,
)
from modules.unit_of_works.base_spreadsheet_unit_of_work import (
    BaseSpreadsheetUnitOfWork,
)


class SomeModuleSpreadsheetUnitOfWork(BaseSpreadsheetUnitOfWork):
    async def __aenter__(self) -> SomeModuleSpreadsheetUnitOfWork:
        await super().__aenter__()
        batch_update_requests = self._batch_update_spreadsheet_session.__enter__()
        self.some_entity_repository = SomeEntityRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        return self

    async def __aexit__(self, *args):
        self.some_entity_repository = None
        await super().__aexit__(*args)
