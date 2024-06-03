from fastapi import APIRouter, Depends

from chore_master_api.models.some_entity import SomeEntity
from chore_master_api.unit_of_works.unit_of_work import SpreadsheetUnitOfWork
from chore_master_api.web_server.dependencies.unit_of_work import get_unit_of_work
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/experiments", tags=["Experiment"])


@router.post("/some_entities", response_model=ResponseSchema[None])
async def post_some_entities(uow: SpreadsheetUnitOfWork = Depends(get_unit_of_work)):
    async with uow:
        some_entity = SomeEntity()
        await uow.some_entity_repository.add(some_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
