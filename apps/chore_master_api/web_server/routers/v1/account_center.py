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


class GetIntegrationOkxTradeResponse(RootModel):
    root: Optional[dict] = None


class UpdateIntegrationOkxTradeRequest(BaseModel):
    class _UpdateAccountRequest(BaseModel):
        env: str
        name: str
        password: str
        passphrase: str
        api_key: str

    accounts: list[_UpdateAccountRequest]


@router.get("/integrations/core")
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


@router.patch("/integrations/core/relational_database")
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
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post("/integrations/core/relational_database/reset")
async def post_integrations_core_relational_database_reset(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
):
    await end_user_db.drop_tables(metadata=end_user_db_registry.metadata)
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post("/integrations/core/relational_database/migrations/generate_revision")
async def post_integrations_core_relational_database_migrations_generate_revision(
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_end_user_db_migration),
):
    try:
        end_user_db_migration.generate_revision(metadata=end_user_db_registry.metadata)
    except alembic.util.exc.CommandError as e:
        raise BadRequestError(str(e))
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post("/integrations/core/relational_database/migrations/upgrade")
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


@router.post("/integrations/core/relational_database/migrations/downgrade")
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


@router.get("/integrations/core/relational_database/migrations/{revision}")
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
    with open(script_path, "r") as f:
        script_content = f.read()
    return ResponseSchema(
        status=StatusEnum.SUCCESS, data={"script_content": script_content}
    )


@router.delete("/integrations/core/relational_database/migrations/{revision}")
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
