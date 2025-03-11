from fastapi import Depends, Request
from sqlalchemy.orm import registry

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.end_user_space.mapper import Mapper
from apps.chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.database.relational_database import (
    DataMigration,
    RelationalDatabase,
    SchemaMigration,
)


async def get_chore_master_db(request: Request) -> RelationalDatabase:
    return request.app.state.chore_master_db


async def get_chore_master_db_registry(
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
) -> registry:
    metadata = RelationalDatabase.create_metadata(
        schema_name=chore_master_api_web_server_config.DATABASE_SCHEMA_NAME
    )
    chore_master_db_registry = RelationalDatabase.create_mapper_registry(
        metadata=metadata
    )
    Mapper(chore_master_db_registry).map_models_to_tables()
    return chore_master_db_registry


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
