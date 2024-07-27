from __future__ import annotations

from apps.chore_master_api.repositories.financial_management import (
    AccountRepository,
    AssetRepository,
    BillRepository,
    NetValueRepository,
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
        self.asset_repository = AssetRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        self.net_value_repository = NetValueRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        self.bill_repository = BillRepository(
            self._google_service, self._spreadsheet_id, batch_update_requests
        )
        return self

    async def __aexit__(self, *args):
        self.bill_repository = None
        self.net_value_repository = None
        self.asset_repository = None
        self.account_repository = None
        await super().__aexit__(*args)
