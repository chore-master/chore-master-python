from fastapi import Depends, Request
from sqlalchemy.orm import registry

from modules.database.relational_database import (
    DataMigration,
    RelationalDatabase,
    SchemaMigration,
)


async def get_chore_master_db(request: Request) -> RelationalDatabase:
    return request.app.state.chore_master_db


async def get_chore_master_db_registry(
    request: Request,
) -> registry:
    return request.app.state.chore_master_db_registry


async def get_schema_migration(
    chore_master_db: RelationalDatabase = Depends(get_chore_master_db),
) -> SchemaMigration:
    schema_migration = SchemaMigration(
        database=chore_master_db,
        version_dir="./apps/chore_master_api/end_user_space/migrations",
        alembic_dir="./apps/chore_master_api/end_user_space/alembic",
    )
    return schema_migration


async def get_data_migration(
    chore_master_db: RelationalDatabase = Depends(get_chore_master_db),
    chore_master_db_registry: registry = Depends(get_chore_master_db_registry),
) -> DataMigration:
    data_migration = DataMigration(chore_master_db, chore_master_db_registry)
    return data_migration
