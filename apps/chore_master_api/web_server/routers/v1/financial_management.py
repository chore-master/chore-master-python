from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from apps.chore_master_api.models.financial_management import Account, Asset, NetValue
from apps.chore_master_api.unit_of_works.financial_management_unit_of_work import (
    FinancialManagementSpreadsheetUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import (
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


class CreateAssetRequest(BaseModel):
    reference: Optional[UUID] = None
    symbol: str


class UpdateAssetRequest(BaseModel):
    symbol: Optional[str] = None


class CreateNetValueRequest(BaseModel):
    reference: Optional[UUID] = None
    account_reference: UUID
    amount: Decimal
    settlement_asset_reference: UUID
    settled_time: Optional[datetime] = None


class UpdateNetValueRequest(BaseModel):
    account_reference: Optional[UUID] = None
    amount: Optional[Decimal] = None
    settlement_asset_reference: Optional[UUID] = None
    settled_time: Optional[datetime] = None


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


@router.get("/assets", response_model=ResponseSchema[list])
async def get_assets(
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        assets = await uow.asset_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=assets,
    )


@router.post("/assets", response_model=ResponseSchema[None])
async def post_assets(
    create_asset_request: CreateAssetRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    asset_dict = {}
    asset_dict.update(create_asset_request.model_dump(exclude_unset=True))
    async with uow:
        asset = Asset(**asset_dict)
        await uow.asset_repository.insert_one(asset)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/assets/{asset_reference}", response_model=ResponseSchema[None])
async def patch_assets_asset_reference(
    asset_reference: Annotated[UUID, Path()],
    update_asset_request: UpdateAssetRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        asset = await uow.asset_repository.find_one(
            filter={"reference": asset_reference}
        )
        updated_entity = asset.model_copy(
            update=update_asset_request.model_dump(exclude_unset=True)
        )
        await uow.asset_repository.update_one(updated_entity=updated_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.delete("/assets/{asset_reference}", response_model=ResponseSchema[None])
async def delete_assets_asset_reference(
    asset_reference: Annotated[UUID, Path()],
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        await uow.asset_repository.delete_many(
            filter={"reference": asset_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.get("/net_values", response_model=ResponseSchema[list])
async def get_net_values(
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        net_values = await uow.net_value_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=net_values,
    )


@router.post("/net_values", response_model=ResponseSchema[None])
async def post_net_values(
    create_net_value_request: CreateNetValueRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    net_value_dict = {"created_time": datetime.utcnow()}
    net_value_dict.update(create_net_value_request.model_dump(exclude_unset=True))
    async with uow:
        net_value = NetValue(**net_value_dict)
        await uow.net_value_repository.insert_one(net_value)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/net_values/{net_value_reference}", response_model=ResponseSchema[None])
async def patch_net_values_net_value_reference(
    net_value_reference: Annotated[UUID, Path()],
    update_net_value_request: UpdateNetValueRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        net_value = await uow.net_value_repository.find_one(
            filter={"reference": net_value_reference}
        )
        updated_entity = net_value.model_copy(
            update=update_net_value_request.model_dump(exclude_unset=True)
        )
        await uow.net_value_repository.update_one(updated_entity=updated_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.delete("/net_values/{net_value_reference}", response_model=ResponseSchema[None])
async def delete_net_values_net_value_reference(
    net_value_reference: Annotated[UUID, Path()],
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        await uow.net_value_repository.delete_many(
            filter={"reference": net_value_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
