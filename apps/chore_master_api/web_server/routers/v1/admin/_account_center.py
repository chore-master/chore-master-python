import os
from typing import Annotated, Literal, Optional

import alembic
from fastapi import APIRouter, Depends, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, RootModel
from sqlalchemy.orm import registry

from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_api_db,
)
from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_end_user_db,
    get_end_user_db_migration,
    get_end_user_db_registry,
)
from apps.chore_master_api.web_server.dependencies.google_service import (
    get_google_service,
)
from modules.database.mongo_client import MongoDB
from modules.database.relational_database import RelationalDatabase, SchemaMigration
from modules.google_service.google_service import GoogleService
from modules.web_server.exceptions import BadRequestError, NotFoundError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()

# @router.get("/integrations/google")
# async def get_integrations_google(
#     current_end_user: dict = Depends(get_current_end_user),
# ):
#     return ResponseSchema[GetIntegrationGoogleResponse](
#         status=StatusEnum.SUCCESS,
#         data=GetIntegrationGoogleResponse(current_end_user.get("google")),
#     )


# @router.get("/integrations/google/drive/folders")
# async def get_integrations_google_drive_folders(
#     folder_name_query: Optional[str] = None,
#     page_token: Optional[str] = None,
#     parent_folder: Optional[str] = None,
#     google_service: GoogleService = Depends(get_google_service),
# ):
#     drive_folder_collection = google_service.get_drive_folder_collection(
#         folder_name_query=folder_name_query,
#         page_token=page_token,
#         parent_folder=parent_folder,
#     )
#     return ResponseSchema[GetIntegrationGoogleDriveFoldersResponse](
#         status=StatusEnum.SUCCESS,
#         data=GetIntegrationGoogleDriveFoldersResponse(
#             metadata=drive_folder_collection.metadata, list=drive_folder_collection.list
#         ),
#     )


# @router.get("/integrations/google/drive/web_view_url")
# async def get_integrations_google_drive_web_view_url(
#     file_id: str,
#     google_service: GoogleService = Depends(get_google_service),
# ):
#     file_dict = google_service.get_drive_file_by_id(file_id)
#     return RedirectResponse(file_dict["webViewLink"])


# @router.get("/integrations/google/spreadsheets/{spreadsheet_name}/spreadsheet_url")
# async def get_integrations_google_spreadsheets_spreadsheet_name_spreadsheet_url(
#     spreadsheet_name: Annotated[Literal["some_module", "financial_management"], Path()],
#     sheet_title: Optional[str] = None,
#     current_end_user: dict = Depends(get_current_end_user),
#     google_service: GoogleService = Depends(get_google_service),
# ):
#     spreadsheet_id = (
#         current_end_user.get("google", {})
#         .get("spreadsheet", {})
#         .get(f"{spreadsheet_name}_spreadsheet_id")
#     )
#     if spreadsheet_id is None:
#         raise NotFoundError(
#             f"spreadsheet `{spreadsheet_name}` is not found in your chore master account"
#         )
#     spreadsheet = google_service.get_spreadsheet(spreadsheet_id)
#     spreadsheet_url = spreadsheet.get("spreadsheetUrl")
#     if spreadsheet_url is None:
#         raise NotFoundError(
#             f"spreadsheet `{spreadsheet_name}` is not found in your google drive"
#         )
#     if sheet_title is not None:
#         sheets = spreadsheet.get("sheets", [])
#         sheet_id = next(
#             (
#                 sheet["properties"]["sheetId"]
#                 for sheet in sheets
#                 if sheet["properties"]["title"] == sheet_title
#             ),
#             None,
#         )
#         if sheet_id is not None:
#             spreadsheet_url = f"{spreadsheet_url}#gid={sheet_id}"
#     return RedirectResponse(spreadsheet_url)


# @router.patch("/integrations/google", response_model=ResponseSchema[None])
# async def patch_integrations_google(
#     update_google: UpdateIntegrationGoogleRequest,
#     current_end_user: dict = Depends(get_current_end_user),
#     google_service: GoogleService = Depends(get_google_service),
#     chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
# ):
#     # Some Module
#     some_module_spreadsheet_file_dict = google_service.migrate_spreadsheet_file(
#         parent_folder_id=update_google.drive_root_folder_id,
#         spreadsheet_name="some_module",
#     )
#     some_module_spreadsheet_id = some_module_spreadsheet_file_dict["id"]
#     google_service.migrate_logical_sheet(
#         some_module_spreadsheet_id, some_entity_logical_sheet
#     )

#     # Financial Management
#     financial_management_spreadsheet_file_dict = (
#         google_service.migrate_spreadsheet_file(
#             parent_folder_id=update_google.drive_root_folder_id,
#             spreadsheet_name="financial_management",
#         )
#     )
#     financial_management_spreadsheet_id = financial_management_spreadsheet_file_dict[
#         "id"
#     ]
#     google_service.migrate_logical_sheet(
#         financial_management_spreadsheet_id, account_logical_sheet
#     )
#     google_service.migrate_logical_sheet(
#         financial_management_spreadsheet_id, asset_logical_sheet
#     )
#     google_service.migrate_logical_sheet(
#         financial_management_spreadsheet_id, net_value_logical_sheet
#     )
#     google_service.migrate_logical_sheet(
#         financial_management_spreadsheet_id, bill_logical_sheet
#     )

#     end_user_collection = chore_master_api_db.get_collection("end_user")
#     await end_user_collection.update_one(
#         filter={"reference": current_end_user["reference"]},
#         update={
#             "$set": {
#                 "is_mounted": True,
#                 "google": {
#                     "drive": {
#                         "root_folder_id": update_google.drive_root_folder_id,
#                     },
#                     "spreadsheet": {
#                         "some_module_spreadsheet_id": some_module_spreadsheet_id,
#                         "financial_management_spreadsheet_id": financial_management_spreadsheet_id,
#                     },
#                 },
#             }
#         },
#     )
#     return ResponseSchema[None](
#         status=StatusEnum.SUCCESS,
#         data=None,
#     )


# @router.get("/integrations/sino_trade")
# async def get_integrations_sino_trade(
#     current_end_user: dict = Depends(get_current_end_user),
# ):
#     return ResponseSchema[GetIntegrationSinoTradeResponse](
#         status=StatusEnum.SUCCESS,
#         data=GetIntegrationSinoTradeResponse(current_end_user.get("sino_trade")),
#     )


# @router.patch("/integrations/sino_trade")
# async def patch_integrations_sino_trade(
#     update_sino_trade: UpdateIntegrationSinoTradeRequest,
#     current_end_user: dict = Depends(get_current_end_user),
#     chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
# ):
#     end_user_collection = chore_master_api_db.get_collection("end_user")
#     await end_user_collection.update_one(
#         filter={"reference": current_end_user["reference"]},
#         update={
#             "$set": {
#                 "sino_trade": {
#                     "account_map": {
#                         account.name: {
#                             "name": account.name,
#                             "api_key": account.api_key,
#                             "secret_key": account.secret_key,
#                         }
#                         for account in update_sino_trade.accounts
#                     }
#                 }
#             }
#         },
#     )
#     return ResponseSchema[None](
#         status=StatusEnum.SUCCESS,
#         data=None,
#     )


# @router.get("/integrations/okx_trade")
# async def get_integrations_okx_trade(
#     current_end_user: dict = Depends(get_current_end_user),
# ):
#     return ResponseSchema[GetIntegrationOkxTradeResponse](
#         status=StatusEnum.SUCCESS,
#         data=GetIntegrationOkxTradeResponse(current_end_user.get("okx_trade")),
#     )


# @router.patch("/integrations/okx_trade")
# async def patch_integrations_okx_trade(
#     update_okx_trade: UpdateIntegrationOkxTradeRequest,
#     current_end_user: dict = Depends(get_current_end_user),
#     chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
# ):
#     end_user_collection = chore_master_api_db.get_collection("end_user")
#     await end_user_collection.update_one(
#         filter={"reference": current_end_user["reference"]},
#         update={
#             "$set": {
#                 "okx_trade": {
#                     "account_map": {
#                         account.name: {
#                             "env": account.env,
#                             "name": account.name,
#                             "password": account.password,
#                             "passphrase": account.passphrase,
#                             "api_key": account.api_key,
#                         }
#                         for account in update_okx_trade.accounts
#                     }
#                 }
#             }
#         },
#     )
#     return ResponseSchema[None](
#         status=StatusEnum.SUCCESS,
#         data=None,
#     )
