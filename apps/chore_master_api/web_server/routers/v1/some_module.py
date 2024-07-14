from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Json

from apps.chore_master_api.models.some_module import SomeEntity
from apps.chore_master_api.unit_of_works.some_module_unit_of_work import (
    SomeModuleSpreadsheetUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
    get_spreadsheet_unit_of_work_factory,
)
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/some_module", tags=["Some Module"])

get_uow = get_spreadsheet_unit_of_work_factory(
    "some_module", SomeModuleSpreadsheetUnitOfWork
)


class CreateSomeEntityRequest(BaseModel):
    reference: Optional[UUID] = None
    a: Optional[bool] = None
    b: Optional[int] = None
    c: Optional[float] = None
    d: Optional[Decimal] = None
    e: Optional[str] = None
    f: Optional[datetime] = None
    g: Optional[str] = None
    h: Optional[int] = None
    i: Optional[dict] = None


class UpdateSomeEntityRequest(BaseModel):
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
    reference: Optional[UUID] = None
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
    reference: Annotated[Optional[UUID], Query()] = None,
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


@router.get("/some_entities", response_model=ResponseSchema[list])
async def get_some_entities(
    filter: SomeEntityFilter = Depends(get_some_entity_filter),
    uow: SomeModuleSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        some_entities = await uow.some_entity_repository.find_many(
            filter=filter.model_dump(exclude_unset=True, exclude_none=True)
        )
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=some_entities,
    )


@router.post("/some_entities", response_model=ResponseSchema[None])
async def post_some_entities(
    create_some_entity_request: CreateSomeEntityRequest,
    uow: SomeModuleSpreadsheetUnitOfWork = Depends(get_uow),
):
    some_entity_dict = {
        "a": True,
        "b": 1,
        "c": 1.5,
        "d": Decimal("9.99"),
        "e": "some string",
        "f": datetime.now(),
        "g": "another string",
        "i": {"key1": 1, "key2": "value2", "key3": [1, 2, 3]},
    }
    some_entity_dict.update(create_some_entity_request.model_dump(exclude_unset=True))
    async with uow:
        some_entity = SomeEntity(**some_entity_dict)
        await uow.some_entity_repository.insert_one(some_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.get("/some_entities/{some_entity_reference}", response_model=ResponseSchema)
async def get_some_entities_some_entity_reference(
    some_entity_reference: Annotated[UUID, Path()],
    uow: SomeModuleSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        some_entity = await uow.some_entity_repository.find_one(
            filter={"reference": some_entity_reference}
        )
    return ResponseSchema(
        status=StatusEnum.SUCCESS,
        data=some_entity,
    )


@router.patch(
    "/some_entities/{some_entity_reference}", response_model=ResponseSchema[None]
)
async def patch_some_entities_some_entity_reference(
    some_entity_reference: Annotated[UUID, Path()],
    update_some_entity_request: UpdateSomeEntityRequest,
    uow: SomeModuleSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        some_entity = await uow.some_entity_repository.find_one(
            filter={"reference": some_entity_reference}
        )
        updated_entity = some_entity.model_copy(
            update=update_some_entity_request.model_dump(exclude_unset=True)
        )
        await uow.some_entity_repository.update_one(updated_entity=updated_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.delete("/some_entities", response_model=ResponseSchema[None])
async def delete_some_entities(
    filter: SomeEntityFilter = Depends(get_some_entity_filter),
    uow: SomeModuleSpreadsheetUnitOfWork = Depends(get_uow),
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


@router.delete(
    "/some_entities/{some_entity_reference}", response_model=ResponseSchema[None]
)
async def delete_some_entities_some_entity_reference(
    some_entity_reference: Annotated[UUID, Path()],
    uow: SomeModuleSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        await uow.some_entity_repository.delete_many(
            filter={"reference": some_entity_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
