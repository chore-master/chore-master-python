from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Account
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.end_user_space import get_finance_uow
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class CreateAccountRequest(BaseCreateEntityRequest):
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: Account.EcosystemTypeEnum


class ReadAccountResponse(BaseQueryEntityResponse):
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: Account.EcosystemTypeEnum


class UpdateAccountRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None
    opened_time: Optional[datetime] = None
    closed_time: Optional[datetime] = None
    ecosystem_type: Optional[Account.EcosystemTypeEnum] = None


@router.get("/accounts")
async def get_accounts(
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        statement = select(Account).order_by(Account.name.asc())
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        return ResponseSchema[list[ReadAccountResponse]](
            status=StatusEnum.SUCCESS,
            data=[entity.model_dump() for entity in entities],
        )


@router.post("/accounts")
async def post_accounts(
    create_entity_request: CreateAccountRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Account(**entity_dict)
        await uow.account_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/accounts/{account_reference}")
async def patch_accounts_account_reference(
    account_reference: Annotated[str, Path()],
    update_entity_request: UpdateAccountRequest,
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.account_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": account_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/accounts/{account_reference}")
async def delete_accounts_account_reference(
    account_reference: Annotated[str, Path()],
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.account_repository.delete_many(
            filter={"reference": account_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
