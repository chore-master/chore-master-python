from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.identity import User
from apps.chore_master_api.end_user_space.models.integration import (
    Resource,
    ResourceDiscriminator,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import get_current_user
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
    get_integration_uow,
)
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.utils.json_utils import JSONUtils
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


# Resource


class CreateResourceRequest(BaseCreateEntityRequest):
    name: str
    discriminator: ResourceDiscriminator
    value: str


class ReadResourceResponse(BaseQueryEntityResponse):
    name: str
    discriminator: ResourceDiscriminator
    value: dict


class UpdateResourceRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None
    discriminator: Optional[ResourceDiscriminator] = None
    value: Optional[str] = None


class ResourceFilter(BaseModel):
    discriminators: list[ResourceDiscriminator]


async def get_resource_filter(
    discriminators: Annotated[Optional[list[ResourceDiscriminator]], Query()] = None,
) -> ResourceFilter:
    return ResourceFilter(
        discriminators=discriminators or [],
    )


# Resource


@router.get("/users/me/resources")
async def get_users_me_resources(
    filter: ResourceFilter = Depends(get_resource_filter),
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
):
    async with uow:
        if len(filter.discriminators) > 0:
            statement = select(Resource).filter(
                Resource.user_reference == current_user.reference,
                Resource.discriminator.in_(filter.discriminators),
            )
            result = await uow.session.execute(statement)
            entities = result.scalars().unique().all()
        else:
            entities = await uow.resource_repository.find_many(
                filter={
                    "user_reference": current_user.reference,
                }
            )
        return ResponseSchema[list[ReadResourceResponse]](
            status=StatusEnum.SUCCESS,
            data=[entity.model_dump() for entity in entities],
        )


@router.post("/users/me/resources")
async def post_users_me_resources(
    create_entity_request: CreateResourceRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
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
        entity = Resource(**entity_dict)
        await uow.resource_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/users/me/resources/{resource_reference}")
async def get_users_me_resources_resource_reference(
    resource_reference: Annotated[str, Path()],
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
):
    async with uow:
        entity = await uow.resource_repository.find_one(
            filter={
                "reference": resource_reference,
                "user_reference": current_user.reference,
            }
        )
        return ResponseSchema(status=StatusEnum.SUCCESS, data=entity.model_dump())


@router.patch("/users/me/resources/{resource_reference}")
async def patch_users_me_resources_resource_reference(
    resource_reference: Annotated[str, Path()],
    update_entity_request: UpdateResourceRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
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
        await uow.resource_repository.update_many(
            values=update_entity_dict,
            filter={
                "reference": resource_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/users/me/resources/{resource_reference}")
async def delete_users_me_resources_resource_reference(
    resource_reference: Annotated[str, Path()],
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_user: User = Depends(get_current_user),
):
    async with uow:
        await uow.resource_repository.delete_many(
            filter={
                "reference": resource_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
