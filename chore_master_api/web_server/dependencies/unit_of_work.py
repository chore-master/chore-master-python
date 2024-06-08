from fastapi import Depends

from chore_master_api.unit_of_works.unit_of_work import SpreadsheetUnitOfWork
from chore_master_api.web_server.dependencies.auth import get_current_end_user
from chore_master_api.web_server.dependencies.google_service import get_google_service
from modules.google_service.google_service import GoogleService
from modules.web_server.exceptions import NotFoundError


async def get_unit_of_work(
    current_end_user: dict = Depends(get_current_end_user),
    google_service: GoogleService = Depends(get_google_service),
) -> SpreadsheetUnitOfWork:
    some_entity_spreadsheet_id = (
        current_end_user.get("google", {})
        .get("spreadsheet", {})
        .get("some_entity_spreadsheet_id")
    )
    if some_entity_spreadsheet_id is None:
        raise NotFoundError("`some_entity_spreadsheet_id` is not set yet")
    return SpreadsheetUnitOfWork(
        google_service=google_service,
        some_entity_spreadsheet_id=some_entity_spreadsheet_id,
    )
