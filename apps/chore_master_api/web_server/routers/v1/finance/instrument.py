from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path

from apps.chore_master_api.end_user_space.models.finance import Instrument
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


class CreateInstrumentRequest(BaseCreateEntityRequest):
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
    quantity_decimals: Optional[int] = None
    price_decimals: Optional[int] = None
    instrument_type: Optional[Instrument.InstrumentTypeEnum] = None
    base_asset_reference: Optional[str] = None
    quote_asset_reference: Optional[str] = None
    settlement_asset_reference: Optional[str] = None
    underlying_asset_reference: Optional[str] = None
    staking_asset_reference: Optional[str] = None
    yielding_asset_reference: Optional[str] = None


@router.get("/instruments")
async def get_instruments(
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        filter = {}
        entities = await uow.instrument_repository.find_many(filter=filter)
        return ResponseSchema[list[ReadInstrumentResponse]](
            status=StatusEnum.SUCCESS, data=[entity.model_dump() for entity in entities]
        )


@router.post("/instruments")
async def post_instruments(
    create_entity_request: CreateInstrumentRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Instrument(**entity_dict)
        await uow.instrument_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/instruments/{instrument_reference}")
async def patch_instruments_instrument_reference(
    instrument_reference: Annotated[str, Path()],
    update_entity_request: UpdateInstrumentRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.instrument_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": instrument_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/instruments/{instrument_reference}")
async def delete_instruments_instrument_reference(
    instrument_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.instrument_repository.delete_many(
            filter={"reference": instrument_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
