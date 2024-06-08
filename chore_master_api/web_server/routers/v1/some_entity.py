from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends

from chore_master_api.models.some_entity import SomeEntity
from chore_master_api.unit_of_works.unit_of_work import SpreadsheetUnitOfWork
from chore_master_api.web_server.dependencies.unit_of_work import get_unit_of_work
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/some_entities", tags=["SomeEntity"])


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
