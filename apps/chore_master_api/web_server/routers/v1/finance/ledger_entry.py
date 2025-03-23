from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from pydantic import ConfigDict
from sqlalchemy import func
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import LedgerEntry
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import require_freemium_role
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
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


class CreateLedgerEntryRequest(BaseCreateEntityRequest):
    entry_time: datetime
    entry_type: LedgerEntry.EntryTypeEnum
    settlement_amount_change: int
    settlement_asset_reference: str
    quantity_change: Optional[int] = None
    instrument_reference: Optional[str] = None
    fill_px: Optional[int] = None
    remark: Optional[str] = None
    parent_ledger_entry_reference: Optional[str] = None


class ReadLedgerEntryResponse(BaseQueryEntityResponse):
    source_type: LedgerEntry.SourceTypeEnum
    entry_time: datetime
    entry_type: LedgerEntry.EntryTypeEnum
    settlement_amount_change: int
    settlement_asset_reference: str
    quantity_change: Optional[int]
    instrument_reference: Optional[str]
    fill_px: Optional[int]
    remark: Optional[str]
    parent_ledger_entry_reference: Optional[str]


class UpdateLedgerEntryRequest(BaseUpdateEntityRequest):
    model_config = ConfigDict(use_enum_values=True)

    entry_type: Optional[LedgerEntry.EntryTypeEnum] = None
    entry_time: Optional[datetime] = None
    settlement_amount_change: Optional[int] = None
    settlement_asset_reference: Optional[str] = None
    quantity_change: Optional[int] = None
    instrument_reference: Optional[str] = None
    fill_px: Optional[int] = None
    remark: Optional[str] = None
    parent_ledger_entry_reference: Optional[str] = None


@router.get(
    "/portfolios/{portfolio_reference}/ledger_entries",
    dependencies=[Depends(require_freemium_role)],
)
async def get_portfolios_portfolio_reference_ledger_entries(
    portfolio_reference: Annotated[str, Path()],
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        filters = [
            LedgerEntry.portfolio_reference == portfolio_reference,
        ]
        count_statement = select(func.count()).select_from(LedgerEntry).where(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(LedgerEntry)
            .where(*filters)
            .order_by(LedgerEntry.entry_time.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadLedgerEntryResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post(
    "/portfolios/{portfolio_reference}/ledger_entries",
    dependencies=[Depends(require_freemium_role)],
)
async def post_portfolios_portfolio_reference_ledger_entries(
    portfolio_reference: Annotated[str, Path()],
    create_entity_request: CreateLedgerEntryRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "portfolio_reference": portfolio_reference,
        "source_type": LedgerEntry.SourceTypeEnum.MANUAL,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = LedgerEntry(**entity_dict)
        await uow.ledger_entry_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/portfolios/{portfolio_reference}/ledger_entries/{ledger_entry_reference}")
async def get_portfolios_portfolio_reference_ledger_entries_ledger_entry_reference(
    portfolio_reference: Annotated[str, Path()],
    ledger_entry_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        entity = await uow.ledger_entry_repository.find_one(
            filter={
                "reference": ledger_entry_reference,
                "portfolio_reference": portfolio_reference,
            }
        )
        response_data = entity.model_dump()
    return ResponseSchema[ReadLedgerEntryResponse](
        status=StatusEnum.SUCCESS, data=response_data
    )


@router.patch(
    "/portfolios/{portfolio_reference}/ledger_entries/{ledger_entry_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_portfolios_portfolio_reference_ledger_entries_ledger_entry_reference(
    portfolio_reference: Annotated[str, Path()],
    ledger_entry_reference: Annotated[str, Path()],
    update_entity_request: UpdateLedgerEntryRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.ledger_entry_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": ledger_entry_reference,
                "portfolio_reference": portfolio_reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/portfolios/{portfolio_reference}/ledger_entries/{ledger_entry_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_portfolios_portfolio_reference_ledger_entries_ledger_entry_reference(
    portfolio_reference: Annotated[str, Path()],
    ledger_entry_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.ledger_entry_repository.delete_many(
            filter={
                "reference": ledger_entry_reference,
                "portfolio_reference": portfolio_reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
