from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Json

from apps.chore_master_api.end_user_space.models.some_module import SomeEntity
from apps.chore_master_api.end_user_space.unit_of_works.some_module import (
    SomeModuleSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_some_module_uow,
)
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/some_module", tags=["Some Module"])


class CreateSomeEntityRequest(BaseCreateEntityRequest):
    a: Optional[bool] = None
    b: Optional[int] = None
    c: Optional[float] = None
    d: Optional[Decimal] = None
    e: Optional[str] = None
    f: Optional[datetime] = None
    g: Optional[str] = None
    h: Optional[int] = None
    i: Optional[dict] = None


class ReadSomeEntityResponse(BaseQueryEntityResponse):
    a: bool
    b: int
    c: float
    d: Decimal
    e: str
    f: datetime
    g: str
    h: Optional[int] = None
    i: Optional[dict] = None


class UpdateSomeEntityRequest(BaseUpdateEntityRequest):
    a: Optional[bool] = None
    b: Optional[int] = None
    c: Optional[float] = None
    d: Optional[Decimal] = None
    e: Optional[str] = None
    f: Optional[datetime] = None
    g: Optional[str] = None
    h: Optional[int] = None
    i: Optional[dict] = None


class SomeEntityFilter(BaseModel):
    reference: Optional[str] = None
    a: Optional[bool] = None
    b: Optional[int] = None
    c: Optional[float] = None
    d: Optional[Decimal] = None
    e: Optional[str] = None
    f: Optional[datetime] = None
    g: Optional[str] = None
    h: Optional[int] = None
    i: Optional[dict] = None


async def get_some_entity_filter(
    reference: Annotated[Optional[str], Query()] = None,
    a: Annotated[Optional[bool], Query()] = None,
    b: Annotated[Optional[int], Query()] = None,
    c: Annotated[Optional[float], Query()] = None,
    d: Annotated[Optional[Decimal], Query()] = None,
    e: Annotated[Optional[str], Query()] = None,
    f: Annotated[Optional[datetime], Query()] = None,
    g: Annotated[Optional[str], Query()] = None,
    h: Annotated[Optional[int], Query()] = None,
    i: Annotated[Optional[Json[Any]], Query()] = None,
) -> SomeEntityFilter:
    return SomeEntityFilter(
        reference=reference, a=a, b=b, c=c, d=d, e=e, f=f, g=g, h=h, i=i
    )


@router.get("/some_entities")
async def get_some_entities(
    filter: SomeEntityFilter = Depends(get_some_entity_filter),
    uow: SomeModuleSQLAlchemyUnitOfWork = Depends(get_some_module_uow),
):
    async with uow:
        entities = await uow.some_entity_repository.find_many(
            filter=filter.model_dump(exclude_unset=True, exclude_none=True)
        )
        return ResponseSchema[list[ReadSomeEntityResponse]](
            status=StatusEnum.SUCCESS, data=[entity.model_dump() for entity in entities]
        )


@router.delete("/some_entities")
async def delete_some_entities(
    filter: SomeEntityFilter = Depends(get_some_entity_filter),
    uow: SomeModuleSQLAlchemyUnitOfWork = Depends(get_some_module_uow),
):
    async with uow:
        await uow.some_entity_repository.delete_many(
            filter=filter.model_dump(exclude_unset=True, exclude_none=True)
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.post("/some_entities")
async def post_some_entities(
    create_entity_request: CreateSomeEntityRequest,
    uow: SomeModuleSQLAlchemyUnitOfWork = Depends(get_some_module_uow),
):
    entity_dict = {
        "a": True,
        "b": 1,
        "c": 1.5,
        "d": Decimal("9.99"),
        "e": "some string",
        "f": datetime.now(),
        "g": "another string",
        "i": {"key1": 1, "key2": "value2", "key3": [1, 2, 3]},
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = SomeEntity(**entity_dict)
        await uow.some_entity_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/some_entities/{some_entity_reference}")
async def get_some_entities_some_entity_reference(
    some_entity_reference: Annotated[str, Path()],
    uow: SomeModuleSQLAlchemyUnitOfWork = Depends(get_some_module_uow),
):
    async with uow:
        entity = await uow.some_entity_repository.find_one(
            filter={"reference": some_entity_reference}
        )
        return ResponseSchema[ReadSomeEntityResponse](
            status=StatusEnum.SUCCESS, data=entity.model_dump()
        )


@router.patch("/some_entities/{some_entity_reference}")
async def patch_some_entities_some_entity_reference(
    some_entity_reference: Annotated[str, Path()],
    update_entity_request: UpdateSomeEntityRequest,
    uow: SomeModuleSQLAlchemyUnitOfWork = Depends(get_some_module_uow),
):
    async with uow:
        await uow.some_entity_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": some_entity_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/some_entities/{some_entity_reference}")
async def delete_some_entities_some_entity_reference(
    some_entity_reference: Annotated[str, Path()],
    uow: SomeModuleSQLAlchemyUnitOfWork = Depends(get_some_module_uow),
):
    async with uow:
        await uow.some_entity_repository.delete_many(
            filter={"reference": some_entity_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
