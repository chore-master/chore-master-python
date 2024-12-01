from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.financial_management import (
    Account,
    Asset,
    Bill,
    NetValue,
)
from apps.chore_master_api.end_user_space.unit_of_works.financial_management import (
    FinancialManagementSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_financial_management_uow,
)
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/financial_management", tags=["Financial Management"])


class CreateAccountRequest(BaseCreateEntityRequest):
    name: str


class ReadAccountResponse(BaseQueryEntityResponse):
    name: str


class UpdateAccountRequest(BaseUpdateEntityRequest):
    name: Optional[str] = None


class CreateAssetRequest(BaseCreateEntityRequest):
    symbol: str


class ReadAssetResponse(BaseQueryEntityResponse):
    symbol: str


class UpdateAssetRequest(BaseUpdateEntityRequest):
    symbol: Optional[str] = None


class CreateNetValueRequest(BaseCreateEntityRequest):
    account_reference: str
    amount: Decimal
    settlement_asset_reference: str
    settled_time: Optional[datetime] = None


class ReadNetValueResponse(BaseQueryEntityResponse):
    account_reference: str
    amount: Decimal
    settlement_asset_reference: str
    settled_time: datetime
    account: ReadAccountResponse
    settlement_asset: ReadAssetResponse


class UpdateNetValueRequest(BaseUpdateEntityRequest):
    account_reference: Optional[str] = None
    amount: Optional[Decimal] = None
    settlement_asset_reference: Optional[str] = None
    settled_time: Optional[datetime] = None


class CreateBillRequest(BaseCreateEntityRequest):
    account_reference: str
    business_type: str
    accounting_type: str
    amount_change: Decimal
    asset_reference: str
    order_reference: Optional[str] = None
    billed_time: datetime


class ReadBillResponse(BaseQueryEntityResponse):
    account_reference: str
    business_type: str
    accounting_type: str
    amount_change: Decimal
    asset_reference: str
    order_reference: Optional[str] = None
    billed_time: datetime


class UpdateBillRequest(BaseUpdateEntityRequest):
    account_reference: Optional[str] = None
    business_type: Optional[str] = None
    accounting_type: Optional[str] = None
    amount_change: Optional[Decimal] = None
    asset_reference: Optional[str] = None
    order_reference: Optional[str] = None
    billed_time: Optional[datetime] = None


@router.get("/accounts", response_model=ResponseSchema[list[ReadAccountResponse]])
async def get_accounts(
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        entities = await uow.account_repository.find_many()
        return ResponseSchema(
            status=StatusEnum.SUCCESS,
            data=[entity.model_dump() for entity in entities],
        )


@router.post("/accounts", response_model=ResponseSchema[None])
async def post_accounts(
    create_entity_request: CreateAccountRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Account(**entity_dict)
        await uow.account_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/accounts/{account_reference}", response_model=ResponseSchema[None])
async def patch_accounts_account_reference(
    account_reference: Annotated[str, Path()],
    update_entity_request: UpdateAccountRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.account_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": account_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/accounts/{account_reference}", response_model=ResponseSchema[None])
async def delete_accounts_account_reference(
    account_reference: Annotated[str, Path()],
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.account_repository.delete_many(
            filter={"reference": account_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/assets", response_model=ResponseSchema[list[ReadAssetResponse]])
async def get_assets(
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        entities = await uow.asset_repository.find_many()
        return ResponseSchema(
            status=StatusEnum.SUCCESS, data=[entity.model_dump() for entity in entities]
        )


@router.post("/assets", response_model=ResponseSchema[None])
async def post_assets(
    create_entity_request: CreateAssetRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Asset(**entity_dict)
        await uow.asset_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/assets/{asset_reference}", response_model=ResponseSchema[None])
async def patch_assets_asset_reference(
    asset_reference: Annotated[str, Path()],
    update_entity_request: UpdateAssetRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.asset_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": asset_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/assets/{asset_reference}", response_model=ResponseSchema[None])
async def delete_assets_asset_reference(
    asset_reference: Annotated[str, Path()],
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.asset_repository.delete_many(
            filter={"reference": asset_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/net_values", response_model=ResponseSchema[list[ReadNetValueResponse]])
async def get_net_values(
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        entities = await uow.net_value_repository.find_many()
        statement = select(NetValue).options(
            joinedload(NetValue.account),
            joinedload(NetValue.settlement_asset),
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        return ResponseSchema(
            status=StatusEnum.SUCCESS,
            data=[
                {
                    **entity.model_dump(),
                    "account": entity.account.model_dump(),
                    "settlement_asset": entity.settlement_asset.model_dump(),
                }
                for entity in entities
            ],
        )


@router.post("/net_values", response_model=ResponseSchema[None])
async def post_net_values(
    create_entity_request: CreateNetValueRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    entity_dict = {"created_time": datetime.utcnow()}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = NetValue(**entity_dict)
        await uow.net_value_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/net_values/{net_value_reference}", response_model=ResponseSchema[None])
async def patch_net_values_net_value_reference(
    net_value_reference: Annotated[str, Path()],
    update_entity_request: UpdateNetValueRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.net_value_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": net_value_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/net_values/{net_value_reference}", response_model=ResponseSchema[None])
async def delete_net_values_net_value_reference(
    net_value_reference: Annotated[str, Path()],
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.net_value_repository.delete_many(
            filter={"reference": net_value_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.get("/bills", response_model=ResponseSchema[list[ReadBillResponse]])
async def get_bills(
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        entities = await uow.bill_repository.find_many()
        return ResponseSchema(
            status=StatusEnum.SUCCESS, data=[entity.model_dump() for entity in entities]
        )


@router.post("/bills", response_model=ResponseSchema[None])
async def post_bills(
    create_entity_request: CreateBillRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    entity_dict = {}
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Bill(**entity_dict)
        await uow.bill_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch("/bills/{bill_reference}", response_model=ResponseSchema[None])
async def patch_bills_bill_reference(
    bill_reference: Annotated[str, Path()],
    update_entity_request: UpdateBillRequest,
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.bill_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={"reference": bill_reference},
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete("/bills/{bill_reference}", response_model=ResponseSchema[None])
async def delete_bills_bill_reference(
    bill_reference: Annotated[str, Path()],
    uow: FinancialManagementSQLAlchemyUnitOfWork = Depends(
        get_financial_management_uow
    ),
):
    async with uow:
        await uow.bill_repository.delete_many(
            filter={"reference": bill_reference}, limit=1
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
