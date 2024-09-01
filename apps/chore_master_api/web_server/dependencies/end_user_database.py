from fastapi import Depends
from sqlalchemy.orm import registry

from apps.chore_master_api.end_user_database.end_user_orm import EndUserORM
from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from modules.database.relational_database import RelationalDatabase, SchemaMigration


async def get_end_user_db_registry(
    current_end_user: dict = Depends(get_current_end_user),
) -> registry:
    core_dict = current_end_user.get("core")
    relational_database_dict = core_dict.get("relational_database", {})
    schema_name = relational_database_dict.get("schema_name")
    metadata = RelationalDatabase.create_metadata(schema_name=schema_name)
    end_user_db_registry = RelationalDatabase.create_mapper_registry(metadata=metadata)
    EndUserORM(end_user_db_registry).map_models_to_tables()
    return end_user_db_registry


async def get_end_user_db(
    current_end_user: dict = Depends(get_current_end_user),
) -> RelationalDatabase:
    core_dict = current_end_user.get("core")
    relational_database_dict = core_dict.get("relational_database", {})
    origin = relational_database_dict.get("origin")
    return RelationalDatabase(origin)


async def get_end_user_db_migration(
    end_user_db: RelationalDatabase = Depends(get_end_user_db, use_cache=False),
) -> SchemaMigration:
    schema_migration = SchemaMigration(
        end_user_db, "./apps/chore_master_api/end_user_database/migrations"
    )
    return schema_migration
