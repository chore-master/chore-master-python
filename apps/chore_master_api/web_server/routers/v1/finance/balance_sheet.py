from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.finance import (
    Account,
    Asset,
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
from modules.utils.string_utils import StringUtils
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class CreateBalanceSheetRequest(BaseCreateEntityRequest):
    class CreateBalanceEntryRequest(BaseCreateEntityRequest):
        account_reference: str
        amount: int

    balanced_time: datetime
    balance_entries: list[CreateBalanceEntryRequest]


class ReadBalanceSheetSummaryResponse(BaseQueryEntityResponse):
    balanced_time: datetime


class ReadBalanceSheetDetailResponse(BaseQueryEntityResponse):
    class ReadBalanceEntryResponse(BaseQueryEntityResponse):
        account_reference: str
        amount: int

    balanced_time: datetime
    balance_entries: list[ReadBalanceEntryResponse]


class UpdateBalanceSheetRequest(BaseUpdateEntityRequest):
    class UpdateBalanceEntryRequest(BaseUpdateEntityRequest):
        account_reference: str
        amount: int

    balanced_time: Optional[datetime] = None
    balance_entries: list[UpdateBalanceEntryRequest]


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
        balance_entries = []
        for be in create_entity_request.balance_entries:
            balance_entry_dict = {
                "balance_sheet_reference": balance_sheet_reference,
            }
            balance_entry_dict.update(be.model_dump(exclude_unset=True))
            balance_entry = BalanceEntry(**balance_entry_dict)
            balance_entries.append(balance_entry)
        await uow.balance_entry_repository.insert_many(balance_entries)

        entity = BalanceSheet(**entity_dict)
        await uow.balance_sheet_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/balance_sheets/series")
async def get_balance_sheets_series(
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = select(BalanceSheet).options(
            joinedload(BalanceSheet.balance_entries),
        )
        result = await uow.session.execute(statement)
        balance_sheets = result.scalars().unique().all()

        balance_entries = [
            balance_entry
            for balance_sheet in balance_sheets
            for balance_entry in balance_sheet.balance_entries
        ]

        account_reference_set = {
            balance_entry.account_reference for balance_entry in balance_entries
        }
        statement = select(Account).filter(Account.reference.in_(account_reference_set))
        result = await uow.session.execute(statement)
        accounts = result.scalars().unique().all()

        asset_reference_set = {
            account.settlement_asset_reference for account in accounts
        }
        statement = select(Asset).filter(Asset.reference.in_(asset_reference_set))
        result = await uow.session.execute(statement)
        assets = result.scalars().unique().all()

        return ResponseSchema[dict](
            status=StatusEnum.SUCCESS,
            data={
                "assets": [asset.model_dump() for asset in assets],
                "accounts": [account.model_dump() for account in accounts],
                "balance_sheets": [
                    balance_sheet.model_dump() for balance_sheet in balance_sheets
                ],
                "balance_entries": [
                    balance_entry.model_dump(mode="json")
                    for balance_entry in balance_entries
                ],
            },
        )


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
    update_entity_dict = update_entity_request.model_dump(
        exclude_unset=True,
        exclude={
            "balance_entries",
        },
    )
    async with uow:
        await uow.balance_entry_repository.delete_many(
            filter={
                "balance_sheet_reference": balance_sheet_reference,
            }
        )
        balance_entries = []
        for be in update_entity_request.balance_entries:
            balance_entry_dict = {
                "balance_sheet_reference": balance_sheet_reference,
            }
            balance_entry_dict.update(be.model_dump(exclude_unset=True))
            balance_entry = BalanceEntry(**balance_entry_dict)
            balance_entries.append(balance_entry)
        await uow.balance_entry_repository.insert_many(balance_entries)
        await uow.balance_sheet_repository.update_many(
            values=update_entity_dict,
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
        await uow.balance_entry_repository.delete_many(
            filter={
                "balance_sheet_reference": balance_sheet_reference,
            }
        )
        await uow.balance_sheet_repository.delete_many(
            filter={"reference": balance_sheet_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
