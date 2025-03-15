from typing import Annotated

from fastapi import APIRouter, Depends, Path

from apps.chore_master_api.end_user_space.models.identity import User, UserRole
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_admin_role,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_identity_uow
from apps.chore_master_api.web_server.schemas.request import BaseCreateEntityRequest
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class CreateUserRoleRequest(BaseCreateEntityRequest):
    user_reference: str
    role_reference: str


@router.post("/user_roles", dependencies=[Depends(require_admin_role)])
async def post_user_roles(
    create_entity_request: CreateUserRoleRequest,
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = UserRole(**entity_dict)
        await uow.user_role_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/user_roles/{user_role_reference}", dependencies=[Depends(require_admin_role)]
)
async def delete_user_roles_user_role_reference(
    user_role_reference: Annotated[str, Path()],
    current_user: User = Depends(get_current_user),
    uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    user_role = next(
        (
            user_role
            for user_role in current_user.user_roles
            if user_role.reference == user_role_reference
        ),
        None,
    )
    if (
        user_role
        and user_role.user_reference == current_user.reference
        and user_role.role.symbol == "ADMIN"
    ):
        raise BadRequestError("Cannot delete your own ADMIN role")
    async with uow:
        await uow.user_role_repository.delete_many(
            filter={"reference": user_role_reference},
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
