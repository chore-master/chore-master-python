from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from apps.chore_master_api.end_user_space.models.identity import User
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.modules.feed_discriminated_resource import (
    FeedDiscriminatedResource,
    IntervalEnum,
)
from apps.chore_master_api.web_server.dependencies.auth import get_current_user
from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_integration_uow,
)
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/users/me")


class FetchPricesRequest(BaseModel):
    target_datetimes: list[datetime]
    target_interval: IntervalEnum
    instrument_symbols: list[str]


# Feed Resource


@router.post("/resources/{resource_reference}/feed/fetch_prices")
async def post_resources_resource_reference_feed_fetch_prices(
    resource_reference: Annotated[str, Path()],
    fetch_prices_request: FetchPricesRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
):
    async with uow:
        resource = await uow.resource_repository.find_one(
            filter={
                "reference": resource_reference,
                "user_reference": current_user.reference,
            }
        )
        feed_resource: FeedDiscriminatedResource = resource.to_discriminated_resource()
        prices = []
        for instrument_symbol in fetch_prices_request.instrument_symbols:
            prices.extend(
                await feed_resource.fetch_prices(
                    instrument_symbol=instrument_symbol,
                    target_interval=fetch_prices_request.target_interval,
                    target_datetimes=fetch_prices_request.target_datetimes,
                )
            )
        return ResponseSchema[list[dict]](
            status=StatusEnum.SUCCESS,
            data=prices,
        )
