from fastapi import Depends
from sqlalchemy.orm import registry

from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_end_user_db,
    get_end_user_db_registry,
)
from modules.database.relational_database import DataMigration, RelationalDatabase


async def get_data_migration(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    end_user_db_registry: registry = Depends(get_end_user_db_registry),
) -> DataMigration:
    data_migration = DataMigration(end_user_db, end_user_db_registry)
    return data_migration
