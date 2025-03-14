from fastapi import Depends
from sqlalchemy.orm import registry

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
from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_db,
    get_chore_master_db_registry,
)
from modules.database.relational_database import RelationalDatabase


async def get_identity_uow(
    chore_master_db: RelationalDatabase = Depends(get_chore_master_db),
    _end_user_db_registry: registry = Depends(get_chore_master_db_registry),
) -> IdentitySQLAlchemyUnitOfWork:
    return IdentitySQLAlchemyUnitOfWork(relational_database=chore_master_db)


async def get_integration_uow(
    chore_master_db: RelationalDatabase = Depends(get_chore_master_db),
    _end_user_db_registry: registry = Depends(get_chore_master_db_registry),
) -> IntegrationSQLAlchemyUnitOfWork:
    return IntegrationSQLAlchemyUnitOfWork(relational_database=chore_master_db)


async def get_finance_uow(
    chore_master_db: RelationalDatabase = Depends(get_chore_master_db),
    _end_user_db_registry: registry = Depends(get_chore_master_db_registry),
) -> FinanceSQLAlchemyUnitOfWork:
    return FinanceSQLAlchemyUnitOfWork(relational_database=chore_master_db)


async def get_some_module_uow(
    chore_master_db: RelationalDatabase = Depends(get_chore_master_db),
    _end_user_db_registry: registry = Depends(get_chore_master_db_registry),
) -> SomeModuleSQLAlchemyUnitOfWork:
    return SomeModuleSQLAlchemyUnitOfWork(relational_database=chore_master_db)
