from fastapi import Depends
from sqlalchemy.orm import registry

from apps.chore_master_api.end_user_space.mapper import Mapper
from apps.chore_master_api.end_user_space.unit_of_works.financial_management import (
    FinancialManagementSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.some_module import (
    SomeModuleSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from modules.database.relational_database import RelationalDatabase, SchemaMigration
from modules.web_server.exceptions import BadRequestError


async def get_end_user_db(
    current_end_user: dict = Depends(get_current_end_user),
) -> RelationalDatabase:
    core_dict = current_end_user.get("core", {})
    relational_database_dict = core_dict.get("relational_database", {})
    origin = relational_database_dict.get("origin")
    if origin is None:
        raise BadRequestError("End user database is not set")
    return RelationalDatabase(origin)


async def get_end_user_db_registry(
    current_end_user: dict = Depends(get_current_end_user),
) -> registry:
    core_dict = current_end_user.get("core", {})
    relational_database_dict = core_dict.get("relational_database", {})
    schema_name = relational_database_dict.get("schema_name")
    metadata = RelationalDatabase.create_metadata(schema_name=schema_name)
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


async def get_financial_management_uow(
    end_user_db: RelationalDatabase = Depends(get_end_user_db),
    _end_user_db_registry: registry = Depends(get_end_user_db_registry),
) -> FinancialManagementSQLAlchemyUnitOfWork:
    return FinancialManagementSQLAlchemyUnitOfWork(relational_database=end_user_db)
