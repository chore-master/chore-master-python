from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from chore_master_api.models.financial_management import Account, Passbook
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
    reference: Optional[UUID] = None
    name: str


class UpdateAccountRequest(BaseModel):
    name: Optional[str] = None


class CreatePassbookRequest(BaseModel):
    account_reference: UUID
    balance_amount: Decimal
    balance_symbol: str
    created_time: Optional[datetime] = None


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
    account_dict = {}
    account_dict.update(create_account_request.model_dump(exclude_unset=True))
    async with uow:
        account = Account(**account_dict)
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


@router.get("/passbooks", response_model=ResponseSchema[list])
async def get_passbooks(
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        passbooks = await uow.passbook_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=passbooks,
    )


@router.post("/passbooks", response_model=ResponseSchema[None])
async def post_passbooks(
    create_passbook_request: CreatePassbookRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    passbook_dict = {"created_time": datetime.utcnow()}
    passbook_dict.update(create_passbook_request.model_dump(exclude_unset=True))
    async with uow:
        passbook = Passbook(**passbook_dict)
        await uow.passbook_repository.insert_one(passbook)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.delete("/passbooks/{passbook_reference}", response_model=ResponseSchema[None])
async def delete_passbooks_passbook_reference(
    passbook_reference: Annotated[UUID, Path()],
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        await uow.passbook_repository.delete_many(
            filter={"reference": passbook_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
