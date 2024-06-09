from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from chore_master_api.models.financial_management import Account
from chore_master_api.unit_of_works.financial_management_unit_of_work import (
    FinancialManagementSpreadsheetUnitOfWork,
)
from chore_master_api.web_server.dependencies.unit_of_work import (
    get_spreadsheet_unit_of_work_factory,
)
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/financial_management", tags=["Financial Management"])

get_uow = get_spreadsheet_unit_of_work_factory(
    "financial_management", FinancialManagementSpreadsheetUnitOfWork
)


class CreateAccountRequest(BaseModel):
    name: str


class UpdateAccountRequest(BaseModel):
    name: Optional[str] = None


@router.get("/accounts", response_model=ResponseSchema[list])
async def get_accounts(
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        accounts = await uow.account_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=accounts,
    )


@router.post("/accounts", response_model=ResponseSchema[None])
async def post_accounts(
    create_account_request: CreateAccountRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        account = Account(name=create_account_request.name)
        await uow.account_repository.insert_one(account)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/accounts/{account_reference}", response_model=ResponseSchema[None])
async def patch_accounts_account_reference(
    account_reference: Annotated[UUID, Path()],
    update_account_request: UpdateAccountRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        account = await uow.account_repository.find_one(
            filter={"reference": account_reference}
        )
        updated_entity = account.model_copy(
            update=update_account_request.model_dump(exclude_unset=True)
        )
        await uow.account_repository.update_one(updated_entity=updated_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.delete("/accounts/{account_reference}", response_model=ResponseSchema[None])
async def delete_accounts_account_reference(
    account_reference: Annotated[UUID, Path()],
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        await uow.account_repository.delete_many(
            filter={"reference": account_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
