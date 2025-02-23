import json
import os
import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import registry

from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_end_user_db,
    get_end_user_db_registry,
)
from modules.database.relational_database import RelationalDatabase
from modules.database.sqlalchemy import types
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


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


def cast_row_dict_to_entity_dict(row_dict: dict, column_name_to_type_map: dict) -> dict:
    entity_dict = {}
    for column_name, raw_value in row_dict.items():
        column_type = column_name_to_type_map[column_name]
        if isinstance(column_type, types.Boolean):
            if raw_value.lower() in [
                "true",
                "1",
                "t",
                "y",
                "yes",
                "on",
                "enable",
                "enabled",
                "active",
                "enabled",
            ]:
                entity_dict[column_name] = True
            elif raw_value.lower() in [
                "false",
                "0",
                "f",
                "n",
                "no",
                "off",
                "disable",
                "disabled",
                "inactive",
                "disabled",
            ]:
                entity_dict[column_name] = False
            else:
                raise BadRequestError(
                    f"Invalid value for boolean column `{column_name}`: {raw_value}"
                )
        elif isinstance(column_type, types.Integer):
            entity_dict[column_name] = int(raw_value)
        elif isinstance(column_type, types.Float):
            entity_dict[column_name] = float(raw_value)
        elif isinstance(column_type, types.DateTime):
            iso_string = raw_value.replace("Z", "")
            entity_dict[column_name] = datetime.fromisoformat(iso_string)
        elif isinstance(column_type, types.String):
            entity_dict[column_name] = str(raw_value)
        elif isinstance(column_type, types.Text):
            entity_dict[column_name] = str(raw_value)
        elif isinstance(column_type, types.JSON):
            entity_dict[column_name] = json.loads(raw_value)
        elif isinstance(column_type, types.DECIMAL):
            entity_dict[column_name] = Decimal(raw_value)
        else:
            raise BadRequestError(f"Unsupported column type: {column_type}")
    return entity_dict


def cast_entity_dict_to_row_dict(
    entity_dict: dict, column_name_to_type_map: dict
) -> dict:
    row_dict = {}
    for column_name, raw_value in entity_dict.items():
        if raw_value is None:
            row_dict[column_name] = None
        else:
            column_type = column_name_to_type_map[column_name]
            if isinstance(column_type, types.Boolean):
                row_dict[column_name] = "true" if raw_value is True else "false"
            elif isinstance(column_type, types.Integer):
                row_dict[column_name] = str(raw_value)
            elif isinstance(column_type, types.Float):
                row_dict[column_name] = str(raw_value)
            elif isinstance(column_type, types.DateTime):
                row_dict[column_name] = f"{raw_value.isoformat()}Z"
            elif isinstance(column_type, types.String):
                row_dict[column_name] = raw_value
            elif isinstance(column_type, types.Text):
                row_dict[column_name] = raw_value
            elif isinstance(column_type, types.JSON):
                row_dict[column_name] = json.dumps(raw_value)
            elif isinstance(column_type, types.DECIMAL):
                str_value = f"{raw_value:f}"  # to remove scientific notation
                if "." in str_value:
                    str_value = str_value.rstrip("0").rstrip(".")
                row_dict[column_name] = str_value
            else:
                raise BadRequestError(f"Unsupported column type: {column_type}")
    return row_dict


@router.get("/database/schema")
async def patch_database_schema(
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
):
    schema_name = end_user_db_registry.metadata.schema
    table_dicts = []
    for full_table_name, table in end_user_db_registry.metadata.tables.items():
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


@router.post("/database/tables/data/export_files")
async def post_database_tables_data_export_files(
    post_database_tables_data_export_files_request: PostDatabaseTablesDataExportFilesRequest,
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
):
    schema_name = end_user_db_registry.metadata.schema
    async_session = end_user_db.get_async_session()
    async with async_session() as session:
        local_directory_path = tempfile.mkdtemp()
        file_name = "download.zip"
        local_file_path = os.path.join(local_directory_path, file_name)
        with tempfile.TemporaryDirectory() as temp_directory_path:
            for (
                table_name,
                selected_column_names,
            ) in (
                post_database_tables_data_export_files_request.table_name_to_selected_column_names.items()
            ):
                if len(selected_column_names) == 0:
                    continue
                full_table_name = (
                    table_name if schema_name is None else f"{schema_name}.{table_name}"
                )
                table = end_user_db_registry.metadata.tables[full_table_name]
                columns = [table.c[col_name] for col_name in selected_column_names]
                column_name_to_type_map = {
                    column.name: column.type for column in columns
                }
                statement = table.select().with_only_columns(*columns)
                result = await session.execute(statement)
                entity_dicts = result.mappings().all()
                if len(entity_dicts) == 0:
                    df = pd.DataFrame(columns=selected_column_names)
                else:
                    row_dicts = [
                        cast_entity_dict_to_row_dict(
                            entity_dict, column_name_to_type_map
                        )
                        for entity_dict in entity_dicts
                    ]
                    df = pd.DataFrame(
                        row_dicts, dtype=str, columns=selected_column_names
                    )
                table_file_path = os.path.join(temp_directory_path, f"{table_name}.csv")
                df.to_csv(table_file_path, index=False)
            shutil.make_archive(
                local_file_path.replace(".zip", ""), "zip", temp_directory_path
            )
        return FileResponse(local_file_path)


@router.patch("/database/tables/data/import_files")
async def patch_database_tables_data_import_files(
    upload_files: list[UploadFile],
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
):
    schema_name = end_user_db_registry.metadata.schema
    async_session = end_user_db.get_async_session()
    async with async_session() as session:
        for upload_file in upload_files:
            file = upload_file.file
            file_name = upload_file.filename.split("/")[-1]
            table_name, _ = os.path.splitext(file_name)
            full_table_name = (
                table_name if schema_name is None else f"{schema_name}.{table_name}"
            )
            table = end_user_db_registry.metadata.tables[full_table_name]
            # pk_columns = [col.name for col in table.primary_key.columns]
            column_name_to_type_map = {
                column.name: column.type for column in table.columns
            }
            df = pd.read_csv(file, dtype=str, keep_default_na=False)
            insert_statements = []
            update_statements = []
            delete_statements = []
            for i, row in enumerate(df.itertuples(index=False)):
                # if getattr(row, "reference", "") == "":
                #     raise BadRequestError(
                #         f"Value is required at table `{table_name}`, column `reference`, row `{i}`"
                #     )
                op = getattr(row, "OP", "")
                op_reference = getattr(row, "OP_REFERENCE", "")
                row_dict = row._asdict()
                row_dict.pop("OP")
                row_dict.pop("OP_REFERENCE")
                entity_dict = cast_row_dict_to_entity_dict(
                    row_dict, column_name_to_type_map
                )
                if op == "INSERT":
                    insert_statements.append(table.insert().values(entity_dict))
                elif op == "UPDATE":
                    if op_reference == "":
                        raise BadRequestError(
                            f"Value is required at table `{table_name}`, column `OP_REFERENCE`, row `{i}`"
                        )
                    # conditions = []
                    # for pk_column in pk_columns:
                    #     pk_value = entity_dict.pop(pk_column)
                    #     conditions.append(table.c[pk_column] == pk_value)
                    # condition = and_(*conditions)
                    condition = table.c["reference"] == op_reference
                    update_statements.append(
                        table.update().where(condition).values(entity_dict)
                    )
                elif op == "DELETE":
                    if op_reference == "":
                        raise BadRequestError(
                            f"Value is required at table `{table_name}`, column `OP_REFERENCE`, row `{i}`"
                        )
                    # conditions = []
                    # for pk_column in pk_columns:
                    #     pk_value = entity_dict.pop(pk_column)
                    #     conditions.append(table.c[pk_column] == pk_value)
                    # condition = and_(*conditions)
                    condition = table.c["reference"] == op_reference
                    delete_statements.append(table.delete().where(condition))
            """
            Debug with following expression:
            `str(statement.compile(compile_kwargs={"literal_binds": True}))`
            """
            try:
                for statement in insert_statements:
                    await session.execute(statement)
                for statement in update_statements:
                    await session.execute(statement)
                for statement in delete_statements:
                    await session.execute(statement)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise BadRequestError(f"Failed to import data: {e}")
    return ResponseSchema(status=StatusEnum.SUCCESS, data=None)
