from fastapi import Depends
from googleapiclient.discovery import Resource

from chore_master_api.unit_of_works.unit_of_work import SpreadsheetUnitOfWork
from chore_master_api.web_server.dependencies.google_service import (
    get_sheets_v4_service,
)


async def get_unit_of_work(
    sheets_service: Resource = Depends(get_sheets_v4_service),
) -> SpreadsheetUnitOfWork:
    return SpreadsheetUnitOfWork(sheets_service=sheets_service)
