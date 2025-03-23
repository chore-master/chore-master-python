import alembic
from sqlalchemy.orm import registry

from modules.database.relational_database import (
    DataMigration,
    RelationalDatabase,
    SchemaMigration,
)
from modules.utils.file_system_utils import FileSystemUtils


async def ensure_system_initialized(
    chore_master_db: RelationalDatabase,
    chore_master_db_registry: registry,
    schema_migration: SchemaMigration,
):
    try:
        applied_revision = schema_migration.applied_revision(
            metadata=chore_master_db_registry.metadata
        )
        if applied_revision is not None:
            return
    except alembic.util.exc.CommandError as e:
        if str(e).startswith("Can't locate revision identified by"):
            # 當實際版本無法匹配任一 scripts 的版本時
            await chore_master_db.drop_tables(
                metadata=chore_master_db_registry.metadata
            )
        else:
            raise NotImplementedError

    all_revisions = schema_migration.all_revisions(
        metadata=chore_master_db_registry.metadata
    )
    if len(all_revisions) == 0:
        await chore_master_db.drop_tables(metadata=chore_master_db_registry.metadata)
        schema_migration.generate_revision(metadata=chore_master_db_registry.metadata)
    schema_migration.upgrade(metadata=chore_master_db_registry.metadata)

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
