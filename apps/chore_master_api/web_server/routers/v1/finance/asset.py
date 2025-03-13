from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, or_
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Asset
from apps.chore_master_api.end_user_space.models.identity import User
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import get_current_user
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


@router.get("/users/me/assets")
async def get_users_me_assets(
    search: Annotated[Optional[str], Query()] = None,
    references: Annotated[Optional[list[str]], Query()] = None,
    is_settleable: Annotated[Optional[bool], Query()] = None,
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    current_user: User = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        filters = [Asset.user_reference == current_user.reference]
        if is_settleable is not None:
            filters.append(Asset.is_settleable == is_settleable)
        if search is not None:
            filters.append(
                or_(
                    Asset.name.ilike(f"%{search}%"),
                    Asset.symbol.ilike(f"%{search}%"),
                )
            )
        if references is not None:
            filters.append(Asset.reference.in_(references))
        count_statement = select(func.count()).select_from(Asset).filter(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Asset)
            .filter(*filters)
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        return ResponseSchema[list[ReadAssetResponse]](
            status=StatusEnum.SUCCESS,
            data=[entity.model_dump() for entity in entities],
            metadata=metadata,
        )


@router.post("/users/me/assets")
async def post_users_me_assets(
    create_entity_request: CreateAssetRequest,
    current_user: User = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "user_reference": current_user.reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Asset(**entity_dict)
        await uow.asset_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/users/me/assets/{asset_reference}")
async def patch_users_me_assets_asset_reference(
    asset_reference: Annotated[str, Path()],
    update_entity_request: UpdateAssetRequest,
    current_user: User = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.asset_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": asset_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/users/me/assets/{asset_reference}")
async def delete_users_me_assets_asset_reference(
    asset_reference: Annotated[str, Path()],
    current_user: User = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.asset_repository.delete_many(
            filter={
                "reference": asset_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
