import os
import shutil
import tempfile
from typing import Annotated, Optional

import alembic
from fastapi import APIRouter, Depends, Path, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import registry

from apps.chore_master_api.web_server.dependencies.auth import require_admin_role
from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_db,
    get_chore_master_db_registry,
    get_data_migration,
    get_schema_migration,
)
from modules.database.relational_database import (
    DataMigration,
    RelationalDatabase,
    SchemaMigration,
)
from modules.web_server.exceptions import BadRequestError, NotFoundError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class ReadDatabaseConnectionResponse(BaseModel):
    all_revisions: list[dict]
    applied_revision: Optional[dict] = None


# class UpdateUserDatabaseConnectionRequest(BaseModel):
#     relational_database_origin: str
#     relational_database_schema_name: Optional[str] = None


class ReadDatabaseSchemaResponse(BaseModel):
    class _Table(BaseModel):
        class _Column(BaseModel):
            name: str
            type: str

        name: str
        columns: list[_Column]

    name: Optional[str] = None
    tables: list[_Table]


class PostDatabaseTablesDataExportFilesRequest(BaseModel):
    table_name_to_selected_column_names: dict[str, list[str]]


@router.post("/database/reset", dependencies=[Depends(require_admin_role)])
async def post_database_reset(
    end_user_db: RelationalDatabase = Depends(get_chore_master_db),
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
):
    await end_user_db.drop_tables(metadata=chore_master_db_registry.metadata)
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get(
    "/database/migrations/revisions", dependencies=[Depends(require_admin_role)]
)
async def get_database_migrations_revisions(
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
    schema_migration: SchemaMigration = Depends(get_schema_migration),
):
    all_revisions = schema_migration.all_revisions(
        metadata=chore_master_db_registry.metadata
    )
    applied_revision = schema_migration.applied_revision(
        metadata=chore_master_db_registry.metadata
    )
    return ResponseSchema[ReadDatabaseConnectionResponse](
        status=StatusEnum.SUCCESS,
        data=ReadDatabaseConnectionResponse(
            all_revisions=all_revisions,
            applied_revision=applied_revision,
        ),
    )


@router.post(
    "/database/migrations/generate_revision",
    dependencies=[Depends(require_admin_role)],
)
async def post_database_migrations_generate_revision(
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
    schema_migration: SchemaMigration = Depends(get_schema_migration),
):
    try:
        schema_migration.generate_revision(metadata=chore_master_db_registry.metadata)
    except alembic.util.exc.CommandError as e:
        raise BadRequestError(str(e))
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post("/database/migrations/upgrade", dependencies=[Depends(require_admin_role)])
async def post_database_migrations_upgrade(
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
    schema_migration: SchemaMigration = Depends(get_schema_migration),
):
    try:
        schema_migration.upgrade(metadata=chore_master_db_registry.metadata)
    except alembic.util.exc.CommandError as e:
        raise BadRequestError(str(e))
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post(
    "/database/migrations/downgrade", dependencies=[Depends(require_admin_role)]
)
async def post_database_migrations_downgrade(
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
    schema_migration: SchemaMigration = Depends(get_schema_migration),
):
    try:
        schema_migration.downgrade(metadata=chore_master_db_registry.metadata)
    except alembic.util.exc.CommandError as e:
        raise BadRequestError(str(e))
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get(
    "/database/migrations/{revision}", dependencies=[Depends(require_admin_role)]
)
async def get_database_migrations_revision(
    revision: Annotated[str, Path()],
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_schema_migration),
):
    all_revisions = end_user_db_migration.all_revisions(
        metadata=chore_master_db_registry.metadata
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


@router.delete(
    "/database/migrations/{revision}", dependencies=[Depends(require_admin_role)]
)
async def delete_database_migrations_revision(
    revision: Annotated[str, Path()],
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
    end_user_db_migration: SchemaMigration = Depends(get_schema_migration),
):
    all_revisions = end_user_db_migration.all_revisions(
        metadata=chore_master_db_registry.metadata
    )
    script_path = next(
        (rev["path"] for rev in all_revisions if rev["revision"] == revision), None
    )
    if script_path is None:
        raise NotFoundError(f"revision `{revision}` is not found")
    os.remove(script_path)
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/database/schema", dependencies=[Depends(require_admin_role)])
async def get_database_schema(
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
):
    schema_name = chore_master_db_registry.metadata.schema
    table_dicts = []
    for full_table_name, table in chore_master_db_registry.metadata.tables.items():
        table_name = full_table_name.split(".")[-1]
        column_dicts = []
        for column in table.columns:
            column_dict = {
                "name": column.name,
                "type": column.type.__class__.__name__,
            }
            column_dicts.append(column_dict)
        table_dict = {
            "name": table_name,
            "columns": column_dicts,
        }
        table_dicts.append(table_dict)
    response_dict = {
        "name": schema_name,
        "tables": table_dicts,
    }
    return ResponseSchema[ReadDatabaseSchemaResponse](
        status=StatusEnum.SUCCESS, data=response_dict
    )


@router.post(
    "/database/tables/data/export_files",
    dependencies=[Depends(require_admin_role)],
)
async def post_database_tables_data_export_files(
    post_database_tables_data_export_files_request: PostDatabaseTablesDataExportFilesRequest,
    data_migration: DataMigration = Depends(get_data_migration),
):
    try:
        local_directory_path = tempfile.mkdtemp()
        file_name: str = "download.zip"
        local_file_path = os.path.join(local_directory_path, file_name)
        with tempfile.TemporaryDirectory() as temp_directory_path:
            await data_migration.export_files(
                table_name_to_selected_column_names=post_database_tables_data_export_files_request.table_name_to_selected_column_names,
                output_directory_path=temp_directory_path,
            )
            shutil.make_archive(
                local_file_path.replace(".zip", ""), "zip", temp_directory_path
            )
        return FileResponse(local_file_path)
    except (ValueError, TypeError) as e:
        raise BadRequestError(str(e))


@router.patch(
    "/database/tables/data/import_files",
    dependencies=[Depends(require_admin_role)],
)
async def patch_database_tables_data_import_files(
    upload_files: list[UploadFile],
    data_migration: DataMigration = Depends(get_data_migration),
):
    try:
        await data_migration.import_files(
            [
                (
                    upload_file.filename.split("/")[-1],
                    upload_file.file,
                )
                for upload_file in upload_files
            ]
        )
        return ResponseSchema(status=StatusEnum.SUCCESS, data=None)
    except (ValueError, TypeError) as e:
        raise BadRequestError(str(e))
