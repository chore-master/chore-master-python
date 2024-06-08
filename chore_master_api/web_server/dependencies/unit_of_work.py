from fastapi import Depends

from chore_master_api.unit_of_works.unit_of_work import SpreadsheetUnitOfWork
from chore_master_api.web_server.dependencies.auth import get_current_end_user
from chore_master_api.web_server.dependencies.google_service import get_google_service
from modules.google_service.google_service import GoogleService
from modules.web_server.exceptions import NotFoundError


def get_unit_of_work_factory(uow_name: str):
    async def _get_unit_of_work(
        current_end_user: dict = Depends(get_current_end_user),
        google_service: GoogleService = Depends(get_google_service),
    ) -> SpreadsheetUnitOfWork:
        uow_spreadsheet_id = (
            current_end_user.get("google", {})
            .get("spreadsheet", {})
            .get(f"{uow_name}_spreadsheet_id")
        )
        if uow_spreadsheet_id is None:
            raise NotFoundError(f"`{uow_name}_spreadsheet_id` is not set yet")
        return SpreadsheetUnitOfWork(
            google_service=google_service,
            spreadsheet_id=uow_spreadsheet_id,
        )

    return _get_unit_of_work
