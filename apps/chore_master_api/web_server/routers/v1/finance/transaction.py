from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from pydantic import Field
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.finance import Transaction, Transfer
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import require_freemium_role
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.trace import (
    Counter,
    get_used_quota_counter,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_finance_uow
from apps.chore_master_api.web_server.schemas.dto import OffsetPagination
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter()


class CreateTransactionRequest(BaseCreateEntityRequest):
    transacted_time: datetime
    chain_id: Optional[str] = None
    tx_hash: Optional[str] = None
    remark: Optional[str] = None


class ReadTransactionResponse(BaseQueryEntityResponse):
    class ReadTransferResponse(BaseQueryEntityResponse):
        flow_type: Transfer.FlowTypeEnum
        asset_amount_change: str
        asset_reference: str
        settlement_asset_amount_change: Optional[str]
        remark: Optional[str]

    portfolio_reference: str
    transacted_time: datetime
    chain_id: Optional[str]
    tx_hash: Optional[str]
    remark: Optional[str]
    transfers: Optional[list[ReadTransferResponse]] = Field(default_factory=list)


class UpdateTransactionRequest(BaseUpdateEntityRequest):
    transacted_time: Optional[datetime] = None
    chain_id: Optional[str] = None
    tx_hash: Optional[str] = None
    remark: Optional[str] = None


@router.get(
    "/portfolios/{portfolio_reference}/transactions",
    dependencies=[Depends(require_freemium_role)],
)
async def get_portfolios_portfolio_reference_transactions(
    portfolio_reference: Annotated[str, Path()],
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        filters = [
            Transaction.portfolio_reference == portfolio_reference,
        ]
        count_statement = select(func.count()).select_from(Transaction).where(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.transacted_time.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
            .options(joinedload(Transaction.transfers))
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [
            {
                **entity.model_dump(),
                "transfers": [transfer.model_dump() for transfer in entity.transfers],
            }
            for entity in entities
        ]
    return ResponseSchema[list[ReadTransactionResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post(
    "/portfolios/{portfolio_reference}/transactions",
    dependencies=[Depends(require_freemium_role)],
)
async def post_portfolios_portfolio_reference_transactions(
    portfolio_reference: Annotated[str, Path()],
    create_entity_request: CreateTransactionRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
    used_quota_counter: Counter = Depends(get_used_quota_counter),
):
    entity_dict = {
        "portfolio_reference": portfolio_reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Transaction(**entity_dict)
        await uow.transaction_repository.insert_one(entity)
        used_quota_counter.increase(1)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch(
    "/portfolios/{portfolio_reference}/transactions/{transaction_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_portfolios_portfolio_reference_transactions_transaction_reference(
    portfolio_reference: Annotated[str, Path()],
    transaction_reference: Annotated[str, Path()],
    update_entity_request: UpdateTransactionRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.transaction_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": transaction_reference,
                "portfolio_reference": portfolio_reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/portfolios/{portfolio_reference}/transactions/{transaction_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_portfolios_portfolio_reference_transactions_transaction_reference(
    portfolio_reference: Annotated[str, Path()],
    transaction_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
    used_quota_counter: Counter = Depends(get_used_quota_counter),
):
    async with uow:
        transfer_count = await uow.transfer_repository.count(
            filter={
                "transaction_reference": transaction_reference,
            },
        )
        used_quota_counter.decrease(transfer_count)

        await uow.transfer_repository.delete_many(
            filter={
                "transaction_reference": transaction_reference,
            },
        )

        await uow.transaction_repository.delete_many(
            filter={
                "reference": transaction_reference,
                "portfolio_reference": portfolio_reference,
            },
            limit=1,
        )
        used_quota_counter.decrease(1)

        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
