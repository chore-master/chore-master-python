from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from pydantic import ConfigDict

from apps.chore_master_api.end_user_space.models.finance import Transfer
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import require_freemium_role
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_finance_uow
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class CreateTransferRequest(BaseCreateEntityRequest):
    flow_type: Transfer.FlowTypeEnum
    asset_amount_change: int
    asset_reference: str
    settlement_asset_amount_change: Optional[int] = None
    remark: Optional[str] = None


class UpdateTransferRequest(BaseUpdateEntityRequest):
    model_config = ConfigDict(use_enum_values=True)

    flow_type: Optional[Transfer.FlowTypeEnum] = None
    asset_amount_change: Optional[int] = None
    asset_reference: Optional[str] = None
    settlement_asset_amount_change: Optional[int] = None
    remark: Optional[str] = None


@router.post(
    "/portfolios/{portfolio_reference}/transactions/{transaction_reference}/transfers",
    dependencies=[Depends(require_freemium_role)],
)
async def post_portfolios_portfolio_reference_transactions_transaction_reference_transfers(
    portfolio_reference: Annotated[str, Path()],
    transaction_reference: Annotated[str, Path()],
    create_entity_request: CreateTransferRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "transaction_reference": transaction_reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Transfer(**entity_dict)
        await uow.transfer_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch(
    "/portfolios/{portfolio_reference}/transactions/{transaction_reference}/transfers/{transfer_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_portfolios_portfolio_reference_transactions_transaction_reference_transfers_transfer_reference(
    portfolio_reference: Annotated[str, Path()],
    transaction_reference: Annotated[str, Path()],
    transfer_reference: Annotated[str, Path()],
    update_entity_request: UpdateTransferRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.transfer_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": transfer_reference,
                "transaction_reference": transaction_reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/portfolios/{portfolio_reference}/transactions/{transaction_reference}/transfers/{transfer_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_portfolios_portfolio_reference_transactions_transaction_reference_transfers_transfer_reference(
    portfolio_reference: Annotated[str, Path()],
    transaction_reference: Annotated[str, Path()],
    transfer_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.transfer_repository.delete_many(
            filter={
                "reference": transfer_reference,
                "transaction_reference": transaction_reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
