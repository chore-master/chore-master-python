from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.integration import (
    Resource,
    ResourceDiscriminator,
)
from apps.chore_master_api.end_user_space.unit_of_works.integration import (
    IntegrationSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from apps.chore_master_api.web_server.dependencies.end_user_space import (
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


@router.get("/end_users/me/resources")
async def get_end_users_me_resources(
    filter: ResourceFilter = Depends(get_resource_filter),
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_end_user: dict = Depends(get_current_end_user),
):
    async with uow:
        if len(filter.discriminators) > 0:
            statement = select(Resource).filter(
                Resource.end_user_reference == current_end_user["reference"],
                Resource.discriminator.in_(filter.discriminators),
            )
            result = await uow.session.execute(statement)
            entities = result.scalars().unique().all()
        else:
            entities = await uow.resource_repository.find_many(
                filter={
                    "end_user_reference": current_end_user["reference"],
                }
            )
        return ResponseSchema[list[ReadResourceResponse]](
            status=StatusEnum.SUCCESS,
            data=[entity.model_dump() for entity in entities],
        )


@router.post("/end_users/me/resources")
async def post_end_users_me_resources(
    create_entity_request: CreateResourceRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_end_user: dict = Depends(get_current_end_user),
):
    try:
        entity_dict = {
            "end_user_reference": current_end_user["reference"],
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


@router.get("/end_users/me/resources/{resource_reference}")
async def get_end_users_me_resources_resource_reference(
    resource_reference: Annotated[str, Path()],
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_end_user: dict = Depends(get_current_end_user),
):
    async with uow:
        entity = await uow.resource_repository.find_one(
            filter={
                "reference": resource_reference,
                "end_user_reference": current_end_user["reference"],
            }
        )
        return ResponseSchema(status=StatusEnum.SUCCESS, data=entity.model_dump())


@router.patch("/end_users/me/resources/{resource_reference}")
async def patch_end_users_me_resources_resource_reference(
    resource_reference: Annotated[str, Path()],
    update_entity_request: UpdateResourceRequest,
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_end_user: dict = Depends(get_current_end_user),
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
                "end_user_reference": current_end_user["reference"],
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/end_users/me/resources/{resource_reference}")
async def delete_end_users_me_resources_resource_reference(
    resource_reference: Annotated[str, Path()],
    uow: IntegrationSQLAlchemyUnitOfWork = Depends(get_integration_uow),
    current_end_user: dict = Depends(get_current_end_user),
):
    async with uow:
        await uow.resource_repository.delete_many(
            filter={
                "reference": resource_reference,
                "end_user_reference": current_end_user["reference"],
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
