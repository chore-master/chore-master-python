from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import ConfigDict
from sqlalchemy import and_, func, or_
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.finance import Account
from apps.chore_master_api.end_user_space.unit_of_works.finance import (
    FinanceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_freemium_role,
)
from apps.chore_master_api.web_server.dependencies.pagination import (
    get_offset_pagination,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_finance_uow
from apps.chore_master_api.web_server.schemas.dto import CurrentUser, OffsetPagination
from apps.chore_master_api.web_server.schemas.request import (
    BaseCreateEntityRequest,
    BaseUpdateEntityRequest,
)
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import (
    MetadataSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter()


class CreateAccountRequest(BaseCreateEntityRequest):
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: Account.EcosystemTypeEnum
    settlement_asset_reference: Optional[str]


class ReadAccountResponse(BaseQueryEntityResponse):
    name: str
    opened_time: datetime
    closed_time: Optional[datetime]
    ecosystem_type: Account.EcosystemTypeEnum
    settlement_asset_reference: str


class UpdateAccountRequest(BaseUpdateEntityRequest):
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = None
    opened_time: Optional[datetime] = None
    closed_time: Optional[datetime] = None
    ecosystem_type: Optional[Account.EcosystemTypeEnum] = None


@router.get("/users/me/accounts", dependencies=[Depends(require_freemium_role)])
async def get_users_me_accounts(
    active_as_of_time: Annotated[Optional[datetime], Query()] = None,
    offset_pagination: OffsetPagination = Depends(get_offset_pagination),
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        filters = [Account.user_reference == current_user.reference]
        if active_as_of_time is not None:
            active_as_of_time = active_as_of_time.replace(tzinfo=None)
            filters.append(
                and_(
                    Account.opened_time <= active_as_of_time,
                    or_(
                        active_as_of_time < Account.closed_time,
                        Account.closed_time == None,
                    ),
                ),
            )
        count_statement = select(func.count()).select_from(Account).filter(*filters)
        count = await uow.session.scalar(count_statement)
        metadata = MetadataSchema(
            offset_pagination=MetadataSchema.OffsetPagination(count=count)
        )
        statement = (
            select(Account)
            .filter(*filters)
            .order_by(Account.closed_time.desc().nulls_first(), Account.name.desc())
            .offset(offset_pagination.offset)
            .limit(offset_pagination.limit)
        )
        result = await uow.session.execute(statement)
        entities = result.scalars().unique().all()
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadAccountResponse]](
        status=StatusEnum.SUCCESS,
        data=response_data,
        metadata=metadata,
    )


@router.post("/users/me/accounts", dependencies=[Depends(require_freemium_role)])
async def post_users_me_accounts(
    create_entity_request: CreateAccountRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    entity_dict = {
        "user_reference": current_user.reference,
    }
    entity_dict.update(create_entity_request.model_dump(exclude_unset=True))
    async with uow:
        entity = Account(**entity_dict)
        await uow.account_repository.insert_one(entity)
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.patch(
    "/users/me/accounts/{account_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def patch_users_me_accounts_account_reference(
    account_reference: Annotated[str, Path()],
    update_entity_request: UpdateAccountRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.account_repository.update_many(
            values=update_entity_request.model_dump(exclude_unset=True),
            filter={
                "reference": account_reference,
                "user_reference": current_user.reference,
            },
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.delete(
    "/users/me/accounts/{account_reference}",
    dependencies=[Depends(require_freemium_role)],
)
async def delete_users_me_accounts_account_reference(
    account_reference: Annotated[str, Path()],
    current_user: CurrentUser = Depends(get_current_user),
    uow: FinanceSQLAlchemyUnitOfWork = Depends(get_finance_uow),
):
    async with uow:
        await uow.account_repository.delete_many(
            filter={
                "reference": account_reference,
                "user_reference": current_user.reference,
            },
            limit=1,
        )
        await uow.commit()
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)
