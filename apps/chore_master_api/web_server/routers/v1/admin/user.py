from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from pydantic import ConfigDict
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.identity import User
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_admin_role,
)
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_identity_uow
from apps.chore_master_api.web_server.schemas.dto import CurrentUser, OffsetPagination
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter()


class CreateUserRequest(BaseCreateEntityRequest):
    reference: Optional[str] = None
    name: str
    username: str
    password: str


class ReadUserSummaryResponse(BaseQueryEntityResponse):
    name: str
    username: str


class ReadUserDetailResponse(BaseQueryEntityResponse):
    class ReadUserRoleResponse(BaseQueryEntityResponse):
        role_reference: str

    name: str
    username: str
    user_roles: list[ReadUserRoleResponse]


class UpdateUserRequest(BaseUpdateEntityRequest):
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


@router.get("/users", dependencies=[Depends(require_admin_role)])
async def get_users(
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    async with uow:
        count_statement = select(func.count()).select_from(User)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(User)
            .order_by(User.created_time.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadUserSummaryResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post("/users", dependencies=[Depends(require_admin_role)])
async def post_users(
    create_entity_request: CreateUserRequest,
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = User(**entity_dict)
        await uow.user_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/users/{user_reference}", dependencies=[Depends(require_admin_role)])
async def get_users_user_reference(
    user_reference: Annotated[str, Path()],
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    async with uow:
        statement = (
            select(User)
            .filter_by(reference=user_reference)
            .options(joinedload(User.user_roles))
        )
        result = await uow.session.execute(statement)
        entity = result.scalars().unique().one()
        response_data = {
            **entity.model_dump(),
            "user_roles": [ur.model_dump(mode="json") for ur in entity.user_roles],
        }
    return ResponseSchema[ReadUserDetailResponse](
        status=StatusEnum.SUCCESS,
        data=response_data,
    )


@router.patch("/users/{user_reference}", dependencies=[Depends(require_admin_role)])
async def patch_users_user_reference(
    user_reference: Annotated[str, Path()],
    update_entity_request: UpdateUserRequest,
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    async with uow:
        await uow.user_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": user_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/users/{user_reference}", dependencies=[Depends(require_admin_role)])
async def delete_users_user_reference(
    user_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    if current_user.reference == user_reference:
        raise BadRequestError("Cannot delete current logged in user")
    async with uow:
        await uow.user_role_repository.delete_many(
            filter={"user_reference": user_reference},
        )
        await uow.user_repository.delete_many(
            filter={"reference": user_reference},
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
