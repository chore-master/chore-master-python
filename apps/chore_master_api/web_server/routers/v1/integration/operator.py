from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.integration import (
    Operator,
    OperatorDiscriminator,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_freemium_role,
)
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
    get_integration_uow,
)
from apps.chore_master_api.web_server.schemas.dto import CurrentUser, OffsetPagination
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.utils.json_utils import JSONUtils
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter()


# Operator


class CreateOperatorRequest(BaseCreateEntityRequest):
    name: str
    discriminator: OperatorDiscriminator
    value: str


class ReadOperatorResponse(BaseQueryEntityResponse):
    name: str
    discriminator: OperatorDiscriminator
    value: dict


class UpdateOperatorRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None
    discriminator: Optional[OperatorDiscriminator] = None
    value: Optional[str] = None


class OperatorFilter(BaseModel):
    discriminators: list[OperatorDiscriminator]


async def get_operator_filter(
    discriminators: Annotated[Optional[list[OperatorDiscriminator]], Query()] = None,
) -> OperatorFilter:
    return OperatorFilter(
        discriminators=discriminators or [],
    )


# Operator


@router.get("/users/me/operators", dependencies=[Depends(require_freemium_role)])
async def get_users_me_operators(
    filter: OperatorFilter = Depends(get_operator_filter),
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    async with uow:
        filters = [Operator.user_reference == current_user.reference]
        if len(filter.discriminators) > 0:
            filters.append(Operator.discriminator.in_(filter.discriminators))
        count_statement = select(func.count()).select_from(Operator).filter(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Operator)
            .filter(*filters)
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadOperatorResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post("/users/me/operators")
async def post_users_me_operators(
    create_entity_request: CreateOperatorRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        entity_dict = {
            "user_reference": current_user.reference,
            "value": JSONUtils.load_json_like(create_entity_request.value),
        }
    except Exception as e:
        raise BadRequestError("Invalid value format, please check the value format.")
    entity_dict.update(
        create_entity_request.model_dump(exclude_unset=True, exclude={"value"})
    )
    async with uow:
        entity = Operator(**entity_dict)
        await uow.operator_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/users/me/operators/{operator_reference}")
async def get_users_me_operators_operator_reference(
    operator_reference: Annotated[str, Path()],
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    async with uow:
        entity = await uow.operator_repository.find_one(
            filter={
                "reference": operator_reference,
                "user_reference": current_user.reference,
            }
        )
        response_data = entity.model_dump()
    return ResponseSchema[dict](status=StatusEnum.SUCCESS, data=response_data)


@router.patch("/users/me/operators/{operator_reference}")
async def patch_users_me_operators_operator_reference(
    operator_reference: Annotated[str, Path()],
    update_entity_request: UpdateOperatorRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    update_entity_dict = update_entity_request.model_dump(exclude_unset=True)
    if "value" in update_entity_dict:
        try:
            update_entity_dict.update(
                {
                    "value": JSONUtils.load_json_like(update_entity_dict["value"]),
                }
            )
        except Exception as e:
            raise BadRequestError(
                "Invalid value format, please check the value format."
            )
    async with uow:
        await uow.operator_repository.update_many(
            values=update_entity_dict,
            filter={
                "reference": operator_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/users/me/operators/{operator_reference}")
async def delete_users_me_operators_operator_reference(
    operator_reference: Annotated[str, Path()],
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    async with uow:
        await uow.operator_repository.delete_many(
            filter={
                "reference": operator_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
