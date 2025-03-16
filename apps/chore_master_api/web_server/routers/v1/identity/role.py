from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.identity import Role
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_identity_uow
from apps.chore_master_api.web_server.schemas.dto import OffsetPagination
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter()


class ReadRoleResponse(BaseQueryEntityResponse):
    symbol: str


@router.get("/roles")
async def get_roles(
    references: Annotated[Optional[list[str]], Query()] = None,
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    async with uow:
        filters = []
        if references is not None:
            filters.append(Role.reference.in_(references))
        count_statement = select(func.count()).select_from(Role).filter(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Role)
            .filter(*filters)
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadRoleResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )
