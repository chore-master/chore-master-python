from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, or_
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Price
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.modules.feed_discriminated_operator import (
    FeedDiscriminatedOperator,
    IntervalEnum,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_freemium_role,
)
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
    get_finance_uow,
    get_integration_uow,
)
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


class AutoFillPriceRequest(BaseUpdateEntityRequest):
    operator_reference: str


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
            .order_by(Price.confirmed_time.desc())
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
    "/users/me/prices/auto-fill",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_users_me_prices_auto_fill(
    auto_fill_price_request: AutoFillPriceRequest,
    current_user: CurrentUser = Depends(get_current_user),
    finance_uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
    integration_uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
):
    async with finance_uow, integration_uow:
        operator = await integration_uow.operator_repository.find_one(
            filter={
                "reference": auto_fill_price_request.operator_reference,
                "user_reference": current_user.reference,
            }
        )
        feed_operator: FeedDiscriminatedOperator = operator.to_discriminated_operator()

        settlable_assets = await finance_uow.asset_repository.find_many(
            filter={
                "user_reference": current_user.reference,
                "is_settleable": True,
            }
        )
        base_asset = next(
            (
                settlable_asset
                for settlable_asset in settlable_assets
                if settlable_asset.symbol == "USD"
            ),
            None,
        )
        quote_assets = [
            settlable_asset
            for settlable_asset in settlable_assets
            if settlable_asset.symbol != "USD"
        ]
        balance_sheets = await finance_uow.balance_sheet_repository.find_many(
            filter={
                "user_reference": current_user.reference,
            }
        )
        occupied_datetimes_set = {
            balance_sheet.balanced_time for balance_sheet in balance_sheets
        }
        for quote_asset in quote_assets:
            prices = await finance_uow.price_repository.find_many(
                filter={
                    "user_reference": current_user.reference,
                    "base_asset_reference": base_asset.reference,
                    "quote_asset_reference": quote_asset.reference,
                },
            )
            existing_datetimes_set = {price.confirmed_time for price in prices}
            target_datetimes = list(occupied_datetimes_set - existing_datetimes_set)
            feed_price_dicts = await feed_operator.fetch_prices(
                instrument_symbol=f"{base_asset.symbol}_{quote_asset.symbol}",
                target_interval=IntervalEnum.PER_1_DAY,
                target_datetimes=target_datetimes,
            )
            for feed_price_dict in feed_price_dicts:
                matched_datetime = feed_price_dict["matched_datetime"]
                if matched_datetime not in existing_datetimes_set:
                    entity = Price(
                        user_reference=current_user.reference,
                        base_asset_reference=base_asset.reference,
                        quote_asset_reference=quote_asset.reference,
                        value=f"{feed_price_dict['matched_price']}",
                        confirmed_time=matched_datetime,
                    )
                    await finance_uow.price_repository.insert_one(entity)
        await finance_uow.commit()
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
        await uow.price_repository.update_many(
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
        await uow.price_repository.delete_many(
            filter={
                "reference": price_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
