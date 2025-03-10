from fastapi import Depends, Request
from sqlalchemy.orm import registry

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.end_user_space.mapper import Mapper
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.some_module import (
    SomeModuleSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.database.relational_database import RelationalDatabase, SchemaMigration


async def get_end_user_db(request: Request) -> RelationalDatabase:
    return request.app.state.chore_master_db


async def get_end_user_db_registry(
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
) -> registry:
    metadata = RelationalDatabase.create_metadata(
        schema_name=chore_master_api_web_server_config.DATABASE_SCHEMA_NAME
    )
    end_user_db_registry = RelationalDatabase.create_mapper_registry(metadata=metadata)
    Mapper(end_user_db_registry).map_models_to_tables()
    return end_user_db_registry


async def get_end_user_db_migration(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
) -> SchemaMigration:
    schema_migration = SchemaMigration(
        database=end_user_db,
        version_dir="./apps/chore_master_api/end_user_space/migrations",
        alembic_dir="./apps/chore_master_api/end_user_space/alembic",
    )
    return schema_migration


async def get_some_module_uow(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    _end_user_db_registry: registry = Depends(get_end_user_db_registry),
) -> SomeModuleSQLAlchemyUnitOfWork:
    return SomeModuleSQLAlchemyUnitOfWork(relational_database=end_user_db)


async def get_integration_uow(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    _end_user_db_registry: registry = Depends(get_end_user_db_registry),
) -> IntegrationSQLAlchemyUnitOfWork:
    return IntegrationSQLAlchemyUnitOfWork(relational_database=end_user_db)


async def get_finance_uow(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    _end_user_db_registry: registry = Depends(get_end_user_db_registry),
) -> FinanceSQLAlchemyUnitOfWork:
    return FinanceSQLAlchemyUnitOfWork(relational_database=end_user_db)


async def get_identity_uow(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    _end_user_db_registry: registry = Depends(get_end_user_db_registry),
) -> IdentitySQLAlchemyUnitOfWork:
    return IdentitySQLAlchemyUnitOfWork(relational_database=end_user_db)
