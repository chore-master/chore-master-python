from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from apps.chore_master_api.end_user_space.models.identity import User
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
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
    get_integration_uow,
)
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/users/me")


class FetchPricesRequest(BaseModel):
    target_datetimes: list[datetime]
    target_interval: IntervalEnum
    instrument_symbols: list[str]


# Feed Operator


@router.post(
    "/operators/{operator_reference}/feed/fetch_prices",
    dependencies=[Depends(require_freemium_role)],
)
async def post_operators_operator_reference_feed_fetch_prices(
    operator_reference: Annotated[str, Path()],
    fetch_prices_request: FetchPricesRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
):
    async with uow:
        operator = await uow.operator_repository.find_one(
            filter={
                "reference": operator_reference,
                "user_reference": current_user.reference,
            }
        )
        feed_operator: FeedDiscriminatedOperator = operator.to_discriminated_operator()
        prices = []
        for instrument_symbol in fetch_prices_request.instrument_symbols:
            prices.extend(
                await feed_operator.fetch_prices(
                    instrument_symbol=instrument_symbol,
                    target_interval=fetch_prices_request.target_interval,
                    target_datetimes=fetch_prices_request.target_datetimes,
                )
            )
        return ResponseSchema[list[dict]](
            status=StatusEnum.SUCCESS,
            data=prices,
        )
