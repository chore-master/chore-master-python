from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel

from chore_master_api.models.some_entity import SomeEntity
from chore_master_api.unit_of_works.unit_of_work import SpreadsheetUnitOfWork
from chore_master_api.web_server.dependencies.unit_of_work import get_unit_of_work
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/some_entities", tags=["SomeEntity"])


class Filter(BaseModel):
    a: Optional[bool] = None
    b: Optional[int] = None
    c: Optional[float] = None
    d: Optional[Decimal] = None
    e: Optional[str] = None
    f: Optional[datetime] = None
    g: Optional[str] = None
    h: Optional[int] = None


async def get_filter(
    a: Annotated[Optional[bool], Query()] = None,
    b: Annotated[Optional[int], Query()] = None,
    c: Annotated[Optional[float], Query()] = None,
    d: Annotated[Optional[Decimal], Query()] = None,
    e: Annotated[Optional[str], Query()] = None,
    f: Annotated[Optional[datetime], Query()] = None,
    g: Annotated[Optional[str], Query()] = None,
    h: Annotated[Optional[int], Query()] = None,
) -> Filter:
    return Filter(a=a, b=b, c=c, d=d, e=e, f=f, g=g, h=h)


@router.get("", response_model=ResponseSchema[list])
async def get_(
    filter: Filter = Depends(get_filter),
    uow: SpreadsheetUnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        some_entities = await uow.some_entity_repository.find_many(
            filter=filter.model_dump(exclude_unset=True, exclude_none=True)
        )
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=some_entities,
    )


@router.post("", response_model=ResponseSchema[None])
async def post_(uow: SpreadsheetUnitOfWork = Depends(get_unit_of_work)):
    async with uow:
        some_entity = SomeEntity(
            a=True,
            b=1,
            c=1.5,
            d=Decimal("2.3"),
            e="a",
            f=datetime.now(),
        )
        await uow.some_entity_repository.insert_one(some_entity)
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.get("/{some_entity_reference}", response_model=ResponseSchema)
async def get_(
    some_entity_reference: Annotated[UUID, Path()],
    uow: SpreadsheetUnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        some_entity = await uow.some_entity_repository.find_one(
            filter={"reference": some_entity_reference}
        )
    return ResponseSchema(
        status=StatusEnum.SUCCESS,
        data=some_entity,
    )
