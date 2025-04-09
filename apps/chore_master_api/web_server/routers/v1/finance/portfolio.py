from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy import func
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Portfolio
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


class CreatePortfolioRequest(BaseCreateEntityRequest):
    name: str
    settlement_asset_reference: str
    description: Optional[str] = None


class ReadPortfolioResponse(BaseQueryEntityResponse):
    name: str
    settlement_asset_reference: str
    description: Optional[str]


class UpdatePortfolioRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("/portfolios", dependencies=[Depends(require_freemium_role)])
async def get_portfolios(
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        count_statement = select(func.count()).select_from(Portfolio)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Portfolio)
            .order_by(Portfolio.created_time.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadPortfolioResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post("/portfolios", dependencies=[Depends(require_freemium_role)])
async def post_portfolios(
    create_entity_request: CreatePortfolioRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "user_reference": current_user.reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Portfolio(**entity_dict)
        await uow.portfolio_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/portfolios/{portfolio_reference}")
async def get_portfolios_portfolio_reference(
    portfolio_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        entity = await uow.portfolio_repository.find_one(
            filter={"reference": portfolio_reference}
        )
        response_data = entity.model_dump()
    return ResponseSchema[ReadPortfolioResponse](
        status=StatusEnum.SUCCESS, data=response_data
    )


@router.patch(
    "/portfolios/{portfolio_reference}", dependencies=[Depends(require_freemium_role)]
)
async def patch_portfolios_portfolio_reference(
    portfolio_reference: Annotated[str, Path()],
    update_entity_request: UpdatePortfolioRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.portfolio_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": portfolio_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/portfolios/{portfolio_reference}", dependencies=[Depends(require_freemium_role)]
)
async def delete_portfolios_portfolio_reference(
    portfolio_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.portfolio_repository.delete_many(
            filter={
                "reference": portfolio_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
