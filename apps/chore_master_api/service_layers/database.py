from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.end_user_space.mapper import Mapper
from apps.chore_master_api.web_server.dependencies.database import get_schema_migration
from modules.database.relational_database import DataMigration, RelationalDatabase
from modules.utils.file_system_utils import FileSystemUtils


async def upgrade():
    chore_master_api_web_server_config = get_chore_master_api_web_server_config()
    chore_master_db = RelationalDatabase(
        chore_master_api_web_server_config.DATABASE_ORIGIN
    )
    metadata = RelationalDatabase.create_metadata(
        schema_name=chore_master_api_web_server_config.DATABASE_SCHEMA_NAME
    )
    chore_master_db_registry = RelationalDatabase.create_mapper_registry(
        metadata=metadata
    )
    Mapper(chore_master_db_registry).map_models_to_tables()

    schema_migration = await get_schema_migration(chore_master_db)
    schema_migration.upgrade(metadata=chore_master_db_registry.metadata)


async def import_data():
    chore_master_api_web_server_config = get_chore_master_api_web_server_config()
    chore_master_db = RelationalDatabase(
        chore_master_api_web_server_config.DATABASE_ORIGIN
    )
    metadata = RelationalDatabase.create_metadata(
        schema_name=chore_master_api_web_server_config.DATABASE_SCHEMA_NAME
    )
    chore_master_db_registry = RelationalDatabase.create_mapper_registry(
        metadata=metadata
    )
    Mapper(chore_master_db_registry).map_models_to_tables()

    data_migration = DataMigration(chore_master_db, chore_master_db_registry)
    for directory in ["global", "admin"]:
        await data_migration.import_files(
            [
                (
                    file_path.split("/")[-1],
                    open(file_path, "rb"),
                )
                for file_path in FileSystemUtils.match_paths(
                    f"apps/chore_master_api/end_user_space/data/{directory}/delete/**/*.csv",
                    recursive=True,
                )
            ]
        )
        await data_migration.import_files(
            [
                (
                    file_path.split("/")[-1],
                    open(file_path, "rb"),
                )
                for file_path in FileSystemUtils.match_paths(
                    f"apps/chore_master_api/end_user_space/data/{directory}/insert/**/*.csv",
                    recursive=True,
                )
            ]
        )
