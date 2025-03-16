from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy import func
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Instrument
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
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter()


class CreateInstrumentRequest(BaseCreateEntityRequest):
    name: str
    quantity_decimals: int
    price_decimals: int
    instrument_type: Instrument.InstrumentTypeEnum
    base_asset_reference: Optional[str] = None
    quote_asset_reference: Optional[str] = None
    settlement_asset_reference: Optional[str] = None
    underlying_asset_reference: Optional[str] = None
    staking_asset_reference: Optional[str] = None
    yielding_asset_reference: Optional[str] = None


class ReadInstrumentResponse(BaseQueryEntityResponse):
    name: str
    quantity_decimals: int
    price_decimals: int
    instrument_type: Instrument.InstrumentTypeEnum
    base_asset_reference: Optional[str]
    quote_asset_reference: Optional[str]
    settlement_asset_reference: Optional[str]
    underlying_asset_reference: Optional[str]
    staking_asset_reference: Optional[str]
    yielding_asset_reference: Optional[str]


class UpdateInstrumentRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None


@router.get("/users/me/instruments", dependencies=[Depends(require_freemium_role)])
async def get_users_me_instruments(
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        count_statement = (
            select(func.count())
            .select_from(Instrument)
            .filter(Instrument.user_reference == current_user.reference)
        )
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Instrument)
            .filter(Instrument.user_reference == current_user.reference)
            .order_by(Instrument.created_time.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        instruments = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in instruments]
    return ResponseSchema[list[ReadInstrumentResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post("/users/me/instruments", dependencies=[Depends(require_freemium_role)])
async def post_users_me_instruments(
    create_entity_request: CreateInstrumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "user_reference": current_user.reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Instrument(**entity_dict)
        await uow.instrument_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch(
    "/users/me/instruments/{instrument_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_users_me_instruments_instrument_reference(
    instrument_reference: Annotated[str, Path()],
    update_entity_request: UpdateInstrumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.instrument_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": instrument_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/users/me/instruments/{instrument_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_users_me_instruments_instrument_reference(
    instrument_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.instrument_repository.delete_many(
            filter={
                "reference": instrument_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
