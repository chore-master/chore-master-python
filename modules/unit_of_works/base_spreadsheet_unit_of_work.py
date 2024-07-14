from __future__ import annotations

from modules.google_service.google_service import GoogleService
from modules.unit_of_works.base_unit_of_work import BaseUnitOfWork


class BaseSpreadsheetUnitOfWork(BaseUnitOfWork):
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

    async def _commit(self):
        self._batch_update_spreadsheet_session.__exit__(None, None, None)

    async def _rollback(self):
        pass
