from typing import Type

from fastapi import Depends

from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from apps.chore_master_api.web_server.dependencies.google_service import (
    get_google_service,
)
from modules.google_service.google_service import GoogleService
from modules.unit_of_works.base_spreadsheet_unit_of_work import (
    BaseSpreadsheetUnitOfWork,
)
from modules.web_server.exceptions import NotFoundError


def get_spreadsheet_unit_of_work_factory(
    uow_name: str, uow_class: Type[BaseSpreadsheetUnitOfWork]
):
    async def _get_spreadsheet_unit_of_work(
        current_end_user: dict = Depends(get_current_end_user),
        google_service: GoogleService = Depends(get_google_service),
    ) -> BaseSpreadsheetUnitOfWork:
        uow_spreadsheet_id = (
            current_end_user.get("google", {})
            .get("spreadsheet", {})
            .get(f"{uow_name}_spreadsheet_id")
        )
        if uow_spreadsheet_id is None:
            raise NotFoundError(f"`{uow_name}_spreadsheet_id` is not set yet")
        return uow_class(
            google_service=google_service,
            spreadsheet_id=uow_spreadsheet_id,
        )

    return _get_spreadsheet_unit_of_work
