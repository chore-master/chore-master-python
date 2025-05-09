from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.finance import (
    BalanceSheet,
    Portfolio,
    Transaction,
)
from apps.chore_master_api.end_user_space.models.trace import Quota
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.trace import (
    TraceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import require_admin_role
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
    get_finance_uow,
    get_integration_uow,
    get_trace_uow,
)
from apps.chore_master_api.web_server.schemas.request import BaseUpdateEntityRequest
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class ReadQuotaResponse(BaseQueryEntityResponse):
    used: int
    limit: int


class UpdateQuotaRequest(BaseUpdateEntityRequest):
    used: Optional[int] = None
    limit: Optional[int] = None


@router.get(
    "/users/{user_reference}/quotas", dependencies=[Depends(require_admin_role)]
)
async def get_quotas(
    user_reference: Annotated[str, Path()],
    uow: TraceSQLAlchemyUnitOfWork = Depends(get_trace_uow),
):
    async with uow:
        entities = await uow.quota_repository.find_many(
            filter={
                "user_reference": user_reference,
            }
        )
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadQuotaResponse]](
        status=StatusEnum.SUCCESS, data=response_data
    )


@router.patch("/quotas/{quota_reference}", dependencies=[Depends(require_admin_role)])
async def patch_quotas_quota_reference(
    quota_reference: Annotated[str, Path()],
    update_entity_request: UpdateQuotaRequest,
    uow: TraceSQLAlchemyUnitOfWork = Depends(get_trace_uow),
):
    async with uow:
        await uow.quota_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": quota_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch(
    "/users/{user_reference}/quotas/recalculate",
    dependencies=[Depends(require_admin_role)],
)
async def patch_users_user_reference_quotas_recalculate(
    user_reference: Annotated[str, Path()],
    trace_uow: TraceSQLAlchemyUnitOfWork = Depends(get_trace_uow),
    integration_uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    finance_uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with trace_uow, integration_uow, finance_uow:
        quotas = await trace_uow.quota_repository.find_many(
            filter={"user_reference": user_reference},
        )

        used = 0

        operators_count = await integration_uow.operator_repository.count(
            filter={"user_reference": user_reference},
        )
        used += operators_count

        accounts_count = await finance_uow.account_repository.count(
            filter={"user_reference": user_reference},
        )
        used += accounts_count

        assets_count = await finance_uow.asset_repository.count(
            filter={"user_reference": user_reference},
        )
        used += assets_count

        statement = (
            select(BalanceSheet)
            .where(
                BalanceSheet.user_reference == user_reference,
            )
            .options(
                joinedload(BalanceSheet.balance_entries),
            )
        )
        result = await finance_uow.session.execute(statement)
        balance_sheets = result.scalars().unique().all()
        used += len(balance_sheets)
        for balance_sheet in balance_sheets:
            used += len(balance_sheet.balance_entries)

        portfolios_count = await finance_uow.portfolio_repository.count(
            filter={"user_reference": user_reference},
        )
        used += portfolios_count

        statement = (
            select(Transaction)
            .join(Portfolio, Transaction.portfolio_reference == Portfolio.reference)
            .where(
                Portfolio.user_reference == user_reference,
            )
            .options(
                joinedload(Transaction.transfers),
            )
        )
        result = await finance_uow.session.execute(statement)
        transactions = result.scalars().unique().all()
        used += len(transactions)
        for transaction in transactions:
            used += len(transaction.transfers)

        if len(quotas) == 0:
            await trace_uow.quota_repository.insert_one(
                Quota(
                    user_reference=user_reference,
                    used=used,
                    limit=0,
                )
            )
        else:
            quota = quotas[0]
            await trace_uow.quota_repository.update_many(
                filter={
                    "reference": quota.reference,
                    "user_reference": user_reference,
                },
                values={"used": used},
            )
        await trace_uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
