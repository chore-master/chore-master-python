from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import or_
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Asset
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


class CreateAssetRequest(BaseCreateEntityRequest):
    name: str
    symbol: str
    decimals: int
    is_settleable: bool


class ReadAssetResponse(BaseQueryEntityResponse):
    name: str
    symbol: str
    decimals: int
    is_settleable: bool


class UpdateAssetRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None
    symbol: Optional[str] = None
    decimals: Optional[int] = None
    is_settleable: Optional[bool] = None


@router.get("/assets")
async def get_assets(
    search: Annotated[Optional[str], Query()] = None,
    references: Annotated[Optional[list[str]], Query()] = None,
    is_settleable: Annotated[Optional[bool], Query()] = None,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = select(Asset)
        if is_settleable is not None:
            statement = statement.filter(Asset.is_settleable == is_settleable)
        if search is not None:
            statement = statement.filter(
                or_(
                    Asset.name.ilike(f"%{search}%"),
                    Asset.symbol.ilike(f"%{search}%"),
                )
            )
        if references is not None:
            statement = statement.filter(Asset.reference.in_(references))
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        return ResponseSchema[list[ReadAssetResponse]](
            status=StatusEnum.SUCCESS, data=[entity.model_dump() for entity in entities]
        )


@router.post("/assets")
async def post_assets(
    create_entity_request: CreateAssetRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Asset(**entity_dict)
        await uow.asset_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/assets/{asset_reference}")
async def patch_assets_asset_reference(
    asset_reference: Annotated[str, Path()],
    update_entity_request: UpdateAssetRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.asset_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": asset_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/assets/{asset_reference}")
async def delete_assets_asset_reference(
    asset_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.asset_repository.delete_many(
            filter={"reference": asset_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
