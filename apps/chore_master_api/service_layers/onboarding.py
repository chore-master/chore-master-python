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
    chore_master_db_migration: SchemaMigration,
):
    applied_revision = chore_master_db_migration.applied_revision(
        metadata=chore_master_db_registry.metadata
    )
    if applied_revision is not None:
        return
    all_revisions = chore_master_db_migration.all_revisions(
        metadata=chore_master_db_registry.metadata
    )
    if len(all_revisions) == 0:
        await chore_master_db.drop_tables(metadata=chore_master_db_registry.metadata)
        chore_master_db_migration.generate_revision(
            metadata=chore_master_db_registry.metadata
        )
    chore_master_db_migration.upgrade(metadata=chore_master_db_registry.metadata)

    data_migration = DataMigration(chore_master_db, chore_master_db_registry)
    file_paths = FileSystemUtils.match_paths(
        "apps/chore_master_api/end_user_space/data/**/*.csv",
        recursive=True,
    )
    await data_migration.import_files(
        [(file_path, open(file_path, "rb")) for file_path in file_paths]
    )
