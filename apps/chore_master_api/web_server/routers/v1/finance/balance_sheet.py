from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

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
from apps.chore_master_api.web_server.schemas.response import (
    BaseQueryEntityResponse,
    SerializableDecimal,
)
from modules.utils.string_utils import StringUtils
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class CreateBalanceSheetRequest(BaseCreateEntityRequest):
    class CreateBalanceEntryRequest(BaseCreateEntityRequest):
        account_reference: str
        asset_reference: str
        entry_type: BalanceEntry.TypeEnum
        amount: Decimal

    balanced_time: datetime
    balance_entries: list[CreateBalanceEntryRequest]


class ReadBalanceSheetSummaryResponse(BaseQueryEntityResponse):
    balanced_time: datetime


class ReadBalanceSheetDetailResponse(BaseQueryEntityResponse):
    class ReadBalanceEntryResponse(BaseQueryEntityResponse):
        account_reference: str
        asset_reference: str
        entry_type: BalanceEntry.TypeEnum
        amount: SerializableDecimal

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
    balance_sheet_reference = StringUtils.new_short_id(8)
    entity_dict = {
        "reference": balance_sheet_reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        for be in create_entity_request.balance_entries:
            balance_entry_dict = {
                "balance_sheet_reference": balance_sheet_reference,
            }
            balance_entry_dict.update(be.model_dump(exclude_unset=True))
            balance_entry = BalanceEntry(**balance_entry_dict)
            await uow.balance_entry_repository.insert_one(balance_entry)

        entity = BalanceSheet(**entity_dict)
        await uow.balance_sheet_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/balance_sheets/{balance_sheet_reference}")
async def get_balance_sheets_balance_sheet_reference(
    balance_sheet_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = (
            select(BalanceSheet)
            .filter_by(
                reference=balance_sheet_reference,
            )
            .options(
                joinedload(BalanceSheet.balance_entries),
            )
        )
        result = await uow.session.execute(statement)
        entity = result.scalars().unique().one()
        return ResponseSchema[ReadBalanceSheetDetailResponse](
            status=StatusEnum.SUCCESS,
            data={
                **entity.model_dump(),
                "balance_entries": [
                    be.model_dump(mode="json") for be in entity.balance_entries
                ],
            },
        )


@router.put("/balance_sheets/{balance_sheet_reference}")
async def put_balance_sheets_balance_sheet_reference(
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
