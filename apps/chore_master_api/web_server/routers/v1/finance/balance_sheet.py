from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.finance import (
    Account,
    BalanceEntry,
    BalanceSheet,
)
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_freemium_role,
)
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_finance_uow
from apps.chore_master_api.web_server.schemas.dto import CurrentUser, OffsetPagination
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.utils.string_utils import StringUtils
from modules.web_server.exceptions import NotFoundError
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

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


@router.get("/users/me/balance_sheets", dependencies=[Depends(require_freemium_role)])
async def get_users_me_balance_sheets(
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = (
            select(BalanceSheet)
            .filter_by(user_reference=current_user.reference)
            .order_by(BalanceSheet.balanced_time.desc())
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadBalanceSheetSummaryResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
    )


@router.post("/users/me/balance_sheets", dependencies=[Depends(require_freemium_role)])
async def post_users_me_balance_sheets(
    create_entity_request: CreateBalanceSheetRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    balance_sheet_reference = StringUtils.new_short_id(8)
    entity_dict = {
        "reference": balance_sheet_reference,
        "user_reference": current_user.reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    entity_dict["balanced_time"] = entity_dict["balanced_time"].replace(tzinfo=None)
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


@router.get(
    "/users/me/balance_sheets/series", dependencies=[Depends(require_freemium_role)]
)
async def get_users_me_balance_sheets_series(
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    async with uow:
        count_statement = (
            select(func.count())
            .select_from(BalanceSheet)
            .filter_by(user_reference=current_user.reference)
        )
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(BalanceSheet)
            .filter_by(user_reference=current_user.reference)
            .order_by(BalanceSheet.balanced_time.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
            .options(
                joinedload(BalanceSheet.balance_entries),
            )
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
        response_data = {
            "accounts": [account.model_dump() for account in accounts],
            "balance_sheets": [
                balance_sheet.model_dump() for balance_sheet in balance_sheets
            ],
            "balance_entries": [
                balance_entry.model_dump(mode="json")
                for balance_entry in balance_entries
            ],
        }
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.get(
    "/users/me/balance_sheets/{balance_sheet_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def get_users_me_balance_sheets_balance_sheet_reference(
    balance_sheet_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = (
            select(BalanceSheet)
            .filter_by(
                reference=balance_sheet_reference,
                user_reference=current_user.reference,
            )
            .options(
                joinedload(BalanceSheet.balance_entries),
            )
        )
        result = await uow.session.execute(statement)
        entity = result.scalars().unique().one()
        response_data = {
            **entity.model_dump(),
            "balance_entries": [
                be.model_dump(mode="json") for be in entity.balance_entries
            ],
        }
    return ResponseSchema[ReadBalanceSheetDetailResponse](
        status=StatusEnum.SUCCESS,
        data=response_data,
    )


@router.put(
    "/users/me/balance_sheets/{balance_sheet_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def put_users_me_balance_sheets_balance_sheet_reference(
    balance_sheet_reference: Annotated[str, Path()],
    update_entity_request: UpdateBalanceSheetRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    update_entity_dict = update_entity_request.model_dump(
        exclude_unset=True,
        exclude={
            "balance_entries",
        },
    )
    update_entity_dict["balanced_time"] = update_entity_dict["balanced_time"].replace(
        tzinfo=None
    )
    async with uow:
        balance_sheet_count = await uow.balance_sheet_repository.count(
            filter={
                "reference": balance_sheet_reference,
                "user_reference": current_user.reference,
            },
        )
        if balance_sheet_count == 0:
            raise NotFoundError("Balance sheet not found")
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
            filter={
                "reference": balance_sheet_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/users/me/balance_sheets/{balance_sheet_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_users_me_balance_sheets_balance_sheet_reference(
    balance_sheet_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        balance_sheet_count = await uow.balance_sheet_repository.count(
            filter={
                "reference": balance_sheet_reference,
                "user_reference": current_user.reference,
            },
        )
        if balance_sheet_count == 0:
            raise NotFoundError("Balance sheet not found")
        await uow.balance_entry_repository.delete_many(
            filter={
                "balance_sheet_reference": balance_sheet_reference,
            }
        )
        await uow.balance_sheet_repository.delete_many(
            filter={
                "reference": balance_sheet_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
