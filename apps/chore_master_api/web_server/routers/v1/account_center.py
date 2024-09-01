import os
from typing import Annotated, Literal, Optional

import alembic
from fastapi import APIRouter, Depends, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, RootModel
from sqlalchemy.orm import registry

# from apps.chore_master_api.logical_sheets.financial_management import (
#     account_logical_sheet,
#     asset_logical_sheet,
#     bill_logical_sheet,
#     net_value_logical_sheet,
# )
# from apps.chore_master_api.logical_sheets.some_module import some_entity_logical_sheet
from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_api_db,
)
from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_end_user_db_migration,
    get_end_user_db_registry,
)
from apps.chore_master_api.web_server.dependencies.google_service import (
    get_google_service,
)
from modules.database.mongo_client import MongoDB
from modules.database.relational_database import SchemaMigration
from modules.google_service.google_service import GoogleService
from modules.web_server.exceptions import BadRequestError, NotFoundError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/account_center", tags=["Account Center"])


class GetIntegrationCoreResponse(BaseModel):
    relational_database_origin: Optional[str] = None
    relational_database_schema_name: Optional[str] = None
    all_revisions: list[dict]
    applied_revision: Optional[dict] = None


class UpdateIntegrationCoreRequest(BaseModel):
    relational_database_origin: str
    relational_database_schema_name: Optional[str] = None


class GetIntegrationGoogleResponse(RootModel):
    root: Optional[dict] = None


class UpdateIntegrationGoogleRequest(BaseModel):
    drive_root_folder_id: str


class GetIntegrationGoogleDriveFoldersResponse(BaseModel):
    class _Metadata(BaseModel):
        next_page_token: Optional[str] = None

    class _Folder(BaseModel):
        id: str
        name: str

    metadata: _Metadata
    list: list[_Folder]


class GetIntegrationSinoTradeResponse(RootModel):
    root: Optional[dict] = None


class UpdateIntegrationSinoTradeRequest(BaseModel):
    class _UpdateAccountRequest(BaseModel):
        name: str
        api_key: str
        secret_key: str

    accounts: list[_UpdateAccountRequest]


@router.get("/end_users/me", response_model=ResponseSchema[dict])
async def get_end_users_me(current_end_user: dict = Depends(get_current_end_user)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "email": current_end_user["email"],
            # "is_mounted": current_end_user.get("is_mounted", False),
        },
    )


@router.get(
    "/integrations/core", response_model=ResponseSchema[GetIntegrationCoreResponse]
)
async def get_integrations_core(
    current_end_user: dict = Depends(get_current_end_user),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_end_user_db_migration),
):
    core_dict = current_end_user.get("core")
    relational_database_dict = core_dict.get("relational_database", {})
    all_revisions = end_user_db_migration.all_revisions(
        metadata=end_user_db_registry.metadata
    )
    applied_revision = end_user_db_migration.applied_revision(
        metadata=end_user_db_registry.metadata
    )
    return ResponseSchema[GetIntegrationCoreResponse](
        status=StatusEnum.SUCCESS,
        data=GetIntegrationCoreResponse(
            relational_database_origin=relational_database_dict.get("origin"),
            relational_database_schema_name=relational_database_dict.get("schema_name"),
            all_revisions=all_revisions,
            applied_revision=applied_revision,
        ),
    )


@router.patch(
    "/integrations/core/relational_database", response_model=ResponseSchema[None]
)
async def patch_integrations_core_relational_database(
    update_core: UpdateIntegrationCoreRequest,
    current_end_user: dict = Depends(get_current_end_user),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    end_user_collection = chore_master_api_db.get_collection("end_user")
    await end_user_collection.update_one(
        filter={"reference": current_end_user["reference"]},
        update={
            "$set": {
                "core": {
                    "relational_database": {
                        "origin": update_core.relational_database_origin,
                        "schema_name": update_core.relational_database_schema_name,
                    },
                },
            }
        },
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.post(
    "/integrations/core/relational_database/migrations/generate_revision",
    response_model=ResponseSchema[None],
)
async def post_integrations_core_relational_database_migrations_generate_revision(
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_end_user_db_migration),
):
    try:
        end_user_db_migration.generate_revision(metadata=end_user_db_registry.metadata)
    except alembic.util.exc.CommandError as e:
        raise BadRequestError(str(e))
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post(
    "/integrations/core/relational_database/migrations/upgrade",
    response_model=ResponseSchema[None],
)
async def post_integrations_core_relational_database_migrations_upgrade(
    # current_end_user: dict = Depends(get_current_end_user),
    # chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_end_user_db_migration),
):
    # end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_db_migration.upgrade(metadata=end_user_db_registry.metadata)
    # await end_user_collection.update_one(
    #     filter={"reference": current_end_user["reference"]},
    #     update={
    #         "$set": {
    #             "is_mounted": True,
    #         }
    #     },
    # )
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post(
    "/integrations/core/relational_database/migrations/downgrade",
    response_model=ResponseSchema[None],
)
async def post_integrations_core_relational_database_migrations_downgrade(
    # current_end_user: dict = Depends(get_current_end_user),
    # chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_end_user_db_migration),
):
    # end_user_collection = chore_master_api_db.get_collection("end_user")
    try:
        end_user_db_migration.downgrade(metadata=end_user_db_registry.metadata)
    except alembic.util.exc.CommandError as e:
        raise BadRequestError(str(e))
    # await end_user_collection.update_one(
    #     filter={"reference": current_end_user["reference"]},
    #     update={
    #         "$set": {
    #             "is_mounted": False,
    #         }
    #     },
    # )
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/integrations/core/relational_database/migrations/{revision}",
    response_model=ResponseSchema[None],
)
async def delete_integrations_core_relational_database_migrations_revision(
    revision: Annotated[str, Path()],
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_end_user_db_migration),
):
    all_revisions = end_user_db_migration.all_revisions(
        metadata=end_user_db_registry.metadata
    )
    script_path = next(
        (rev["path"] for rev in all_revisions if rev["revision"] == revision), None
    )
    if script_path is None:
        raise NotFoundError(f"revision `{revision}` is not found")
    os.remove(script_path)
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get(
    "/integrations/google", response_model=ResponseSchema[GetIntegrationGoogleResponse]
)
async def get_integrations_google(
    current_end_user: dict = Depends(get_current_end_user),
):
    return ResponseSchema[GetIntegrationGoogleResponse](
        status=StatusEnum.SUCCESS,
        data=GetIntegrationGoogleResponse(current_end_user.get("google")),
    )


@router.get(
    "/integrations/google/drive/folders",
    response_model=ResponseSchema[GetIntegrationGoogleDriveFoldersResponse],
)
async def get_integrations_google_drive_folders(
    folder_name_query: Optional[str] = None,
    page_token: Optional[str] = None,
    parent_folder: Optional[str] = None,
    google_service: GoogleService = Depends(get_google_service),
):
    drive_folder_collection = google_service.get_drive_folder_collection(
        folder_name_query=folder_name_query,
        page_token=page_token,
        parent_folder=parent_folder,
    )
    return ResponseSchema[GetIntegrationGoogleDriveFoldersResponse](
        status=StatusEnum.SUCCESS,
        data=GetIntegrationGoogleDriveFoldersResponse(
            metadata=drive_folder_collection.metadata, list=drive_folder_collection.list
        ),
    )


@router.get("/integrations/google/drive/web_view_url")
async def get_integrations_google_drive_web_view_url(
    file_id: str,
    google_service: GoogleService = Depends(get_google_service),
):
    file_dict = google_service.get_drive_file_by_id(file_id)
    return RedirectResponse(file_dict["webViewLink"])


@router.get("/integrations/google/spreadsheets/{spreadsheet_name}/spreadsheet_url")
async def get_integrations_google_spreadsheets_spreadsheet_name_spreadsheet_url(
    spreadsheet_name: Annotated[Literal["some_module", "financial_management"], Path()],
    sheet_title: Optional[str] = None,
    current_end_user: dict = Depends(get_current_end_user),
    google_service: GoogleService = Depends(get_google_service),
):
    spreadsheet_id = (
        current_end_user.get("google", {})
        .get("spreadsheet", {})
        .get(f"{spreadsheet_name}_spreadsheet_id")
    )
    if spreadsheet_id is None:
        raise NotFoundError(
            f"spreadsheet `{spreadsheet_name}` is not found in your chore master account"
        )
    spreadsheet = google_service.get_spreadsheet(spreadsheet_id)
    spreadsheet_url = spreadsheet.get("spreadsheetUrl")
    if spreadsheet_url is None:
        raise NotFoundError(
            f"spreadsheet `{spreadsheet_name}` is not found in your google drive"
        )
    if sheet_title is not None:
        sheets = spreadsheet.get("sheets", [])
        sheet_id = next(
            (
                sheet["properties"]["sheetId"]
                for sheet in sheets
                if sheet["properties"]["title"] == sheet_title
            ),
            None,
        )
        if sheet_id is not None:
            spreadsheet_url = f"{spreadsheet_url}#gid={sheet_id}"
    return RedirectResponse(spreadsheet_url)


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


@router.get(
    "/integrations/sino_trade",
    response_model=ResponseSchema[GetIntegrationSinoTradeResponse],
)
async def get_integrations_sino_trade(
    current_end_user: dict = Depends(get_current_end_user),
):
    return ResponseSchema[GetIntegrationSinoTradeResponse](
        status=StatusEnum.SUCCESS,
        data=GetIntegrationSinoTradeResponse(current_end_user.get("sino_trade")),
    )


@router.patch("/integrations/sino_trade", response_model=ResponseSchema[None])
async def patch_integrations_sino_trade(
    update_sino_trade: UpdateIntegrationSinoTradeRequest,
    current_end_user: dict = Depends(get_current_end_user),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    end_user_collection = chore_master_api_db.get_collection("end_user")
    await end_user_collection.update_one(
        filter={"reference": current_end_user["reference"]},
        update={
            "$set": {
                "sino_trade": {
                    "account_map": {
                        account.name: {
                            "name": account.name,
                            "api_key": account.api_key,
                            "secret_key": account.secret_key,
                        }
                        for account in update_sino_trade.accounts
                    }
                }
            }
        },
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
