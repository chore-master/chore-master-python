from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from apps.chore_master_api.models.financial_management import (
    Account,
    Asset,
    Bill,
    NetValue,
)
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


class CreateBillRequest(BaseModel):
    reference: Optional[UUID] = None
    account_reference: UUID
    business_type: str
    accounting_type: str
    amount_change: Decimal
    asset_reference: UUID
    order_reference: Optional[str] = None
    billed_time: datetime


class UpdateBillRequest(BaseModel):
    account_reference: Optional[UUID] = None
    business_type: Optional[str] = None
    accounting_type: Optional[str] = None
    amount_change: Optional[Decimal] = None
    asset_reference: Optional[UUID] = None
    order_reference: Optional[str] = None
    billed_time: Optional[datetime] = None


@router.get("/accounts", response_model=ResponseSchema[list])
async def get_accounts(
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        entities = await uow.account_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=entities,
    )


@router.post("/accounts", response_model=ResponseSchema[None])
async def post_accounts(
    create_entity_request: CreateAccountRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Account(**entity_dict)
        await uow.account_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/accounts/{account_reference}", response_model=ResponseSchema[None])
async def patch_accounts_account_reference(
    account_reference: Annotated[UUID, Path()],
    update_entity_request: UpdateAccountRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        entity = await uow.account_repository.find_one(
            filter={"reference": account_reference}
        )
        updated_entity = entity.model_copy(
            update=update_entity_request.model_dump(exclude_unset=True)
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
        entities = await uow.asset_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=entities,
    )


@router.post("/assets", response_model=ResponseSchema[None])
async def post_assets(
    create_entity_request: CreateAssetRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Asset(**entity_dict)
        await uow.asset_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/assets/{asset_reference}", response_model=ResponseSchema[None])
async def patch_assets_asset_reference(
    asset_reference: Annotated[UUID, Path()],
    update_entity_request: UpdateAssetRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        entity = await uow.asset_repository.find_one(
            filter={"reference": asset_reference}
        )
        updated_entity = entity.model_copy(
            update=update_entity_request.model_dump(exclude_unset=True)
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
        entities = await uow.net_value_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=entities,
    )


@router.post("/net_values", response_model=ResponseSchema[None])
async def post_net_values(
    create_entity_request: CreateNetValueRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    entity_dict = {"created_time": datetime.utcnow()}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = NetValue(**entity_dict)
        await uow.net_value_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/net_values/{net_value_reference}", response_model=ResponseSchema[None])
async def patch_net_values_net_value_reference(
    net_value_reference: Annotated[UUID, Path()],
    update_entity_request: UpdateNetValueRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        entity = await uow.net_value_repository.find_one(
            filter={"reference": net_value_reference}
        )
        updated_entity = entity.model_copy(
            update=update_entity_request.model_dump(exclude_unset=True)
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


@router.get("/bills", response_model=ResponseSchema[list])
async def get_bills(
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        entities = await uow.bill_repository.find_many()
    return ResponseSchema[list](
        status=StatusEnum.SUCCESS,
        data=entities,
    )


@router.post("/bills", response_model=ResponseSchema[None])
async def post_bills(
    create_entity_request: CreateBillRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Bill(**entity_dict)
        await uow.bill_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.patch("/bills/{bill_reference}", response_model=ResponseSchema[None])
async def patch_bills_bill_reference(
    bill_reference: Annotated[UUID, Path()],
    update_entity_request: UpdateBillRequest,
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        entity = await uow.bill_repository.find_one(
            filter={"reference": bill_reference}
        )
        updated_entity = entity.model_copy(
            update=update_entity_request.model_dump(exclude_unset=True)
        )
        await uow.bill_repository.update_one(updated_entity=updated_entity)
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.delete("/bills/{bill_reference}", response_model=ResponseSchema[None])
async def delete_bills_bill_reference(
    bill_reference: Annotated[UUID, Path()],
    uow: FinancialManagementSpreadsheetUnitOfWork = Depends(get_uow),
):
    async with uow:
        await uow.bill_repository.delete_many(
            filter={"reference": bill_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
