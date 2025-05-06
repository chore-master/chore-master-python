from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, or_
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Price
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


class CreatePriceRequest(BaseCreateEntityRequest):
    base_asset_reference: str
    quote_asset_reference: str
    value: str
    confirmed_time: datetime


class ReadPriceResponse(BaseQueryEntityResponse):
    base_asset_reference: str
    quote_asset_reference: str
    value: str
    confirmed_time: datetime


class UpdatePriceRequest(BaseUpdateEntityRequest):
    base_asset_reference: Optional[str] = None
    quote_asset_reference: Optional[str] = None
    value: Optional[str] = None
    confirmed_time: Optional[datetime] = None


@router.get("/users/me/prices", dependencies=[Depends(require_freemium_role)])
async def get_users_me_prices(
    base_asset_reference: Annotated[Optional[str], Query()] = None,
    quote_asset_reference: Annotated[Optional[str], Query()] = None,
    gte_confirmed_time: Annotated[Optional[datetime], Query()] = None,
    lt_confirmed_time: Annotated[Optional[datetime], Query()] = None,
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        filters = [Price.user_reference == current_user.reference]
        if base_asset_reference is not None:
            filters.append(Price.base_asset_reference == base_asset_reference)
        if quote_asset_reference is not None:
            filters.append(Price.quote_asset_reference == quote_asset_reference)
        if gte_confirmed_time is not None:
            filters.append(Price.confirmed_time >= gte_confirmed_time)
        if lt_confirmed_time is not None:
            filters.append(Price.confirmed_time < lt_confirmed_time)
        count_statement = select(func.count()).select_from(Price).filter(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Price)
            .filter(*filters)
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadPriceResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post("/users/me/prices", dependencies=[Depends(require_freemium_role)])
async def post_users_me_prices(
    create_entity_request: CreatePriceRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "user_reference": current_user.reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Price(**entity_dict)
        await uow.price_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch(
    "/users/me/prices/{price_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_users_me_prices_price_reference(
    price_reference: Annotated[str, Path()],
    update_entity_request: UpdatePriceRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.asset_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": price_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/users/me/prices/{price_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_users_me_prices_price_reference(
    price_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.asset_repository.delete_many(
            filter={
                "reference": price_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
