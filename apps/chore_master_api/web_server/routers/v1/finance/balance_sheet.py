from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import (
    BalanceEntry,
    BalanceSheet,
)
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.end_user_space import get_finance_uow
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class CreateBalanceSheetRequest(BaseCreateEntityRequest):
    balanced_time: datetime


class ReadBalanceSheetSummaryResponse(BaseQueryEntityResponse):
    balanced_time: datetime


class ReadBalanceSheetDetailResponse(BaseQueryEntityResponse):
    class ReadBalanceEntryResponse(BaseQueryEntityResponse):
        entry_type: BalanceEntry.TypeEnum
        amount: Decimal

    balanced_time: datetime
    balance_entries: list[ReadBalanceEntryResponse]


class UpdateBalanceSheetRequest(BaseUpdateEntityRequest):
    balanced_time: Optional[datetime] = None


@router.get("/balance_sheets")
async def get_balance_sheets(
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = select(BalanceSheet).order_by(BalanceSheet.balanced_time.desc())
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        return ResponseSchema[list[ReadBalanceSheetSummaryResponse]](
            status=StatusEnum.SUCCESS,
            data=[entity.model_dump() for entity in entities],
        )


@router.post("/balance_sheets")
async def post_balance_sheets(
    create_entity_request: CreateBalanceSheetRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = BalanceSheet(**entity_dict)
        await uow.balance_sheet_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/balance_sheets/{balance_sheet_reference}")
async def patch_balance_sheets_balance_sheet_reference(
    balance_sheet_reference: Annotated[str, Path()],
    update_entity_request: UpdateBalanceSheetRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.balance_sheet_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": balance_sheet_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/balance_sheets/{balance_sheet_reference}")
async def delete_balance_sheets_balance_sheet_reference(
    balance_sheet_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.balance_sheet_repository.delete_many(
            filter={"reference": balance_sheet_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
