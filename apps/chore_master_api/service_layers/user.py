from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.trace import (
    TraceSQLAlchemyUnitOfWork,
)


async def migrate_user_reference(
    old_user_reference: str,
    new_user_reference: str,
    identity_uow: IdentitySQLAlchemyUnitOfWork,
    trace_uow: TraceSQLAlchemyUnitOfWork,
    finance_uow: FinanceSQLAlchemyUnitOfWork,
    integration_uow: IntegrationSQLAlchemyUnitOfWork,
):
    # identity module
    async with identity_uow:
        await identity_uow.user_role_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await identity_uow.user_session_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await identity_uow.user_attribute_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await identity_uow.commit()

    # integration module
    async with integration_uow:
        await integration_uow.operator_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await integration_uow.commit()

    # trace module
    async with trace_uow:
        await trace_uow.quota_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await trace_uow.commit()

    # finance module
    async with finance_uow:
        await finance_uow.account_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await finance_uow.asset_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await finance_uow.balance_sheet_repository.update_many(
            filter={"user_reference": old_user_reference},
            values={"user_reference": new_user_reference},
        )
        await finance_uow.commit()
