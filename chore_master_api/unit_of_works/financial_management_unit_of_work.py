from __future__ import annotations

from chore_master_api.repositories.financial_management import (
    AccountRepository,
    PassbookRepository,
)
from modules.unit_of_works.base_spreadsheet_unit_of_work import (
    BaseSpreadsheetUnitOfWork,
)


class FinancialManagementSpreadsheetUnitOfWork(BaseSpreadsheetUnitOfWork):
    async def __aenter__(self) -> FinancialManagementSpreadsheetUnitOfWork:
        await super().__aenter__()
        batch_update_requests = self._batch_update_spreadsheet_session.__enter__()
        self.account_repository = AccountRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        self.passbook_repository = PassbookRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        return self

    async def __aexit__(self, *args):
        self.passbook_repository = None
        self.account_repository = None
        await super().__aexit__(*args)
