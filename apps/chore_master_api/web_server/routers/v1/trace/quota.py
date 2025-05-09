from fastapi import APIRouter, Depends

from apps.chore_master_api.end_user_space.unit_of_works.trace import (
    TraceSQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.auth import (
    get_current_user,
    require_freemium_role,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_trace_uow
from apps.chore_master_api.web_server.schemas.dto import CurrentUser
from apps.chore_master_api.web_server.schemas.response import BaseQueryEntityResponse
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


# Quota


class ReadQuotaResponse(BaseQueryEntityResponse):
    used: int
    limit: int


# Quota


@router.get("/users/me/quotas", dependencies=[Depends(require_freemium_role)])
async def get_users_me_quotas(
    uow: TraceSQLAlchemyUnitOfWork = Depends(get_trace_uow),
    current_user: CurrentUser = Depends(get_current_user),
):
    async with uow:
        entities = await uow.quota_repository.find_many(
            filter={
                "user_reference": current_user.reference,
            }
        )
        response_data = [entity.model_dump() for entity in entities]
    return ResponseSchema[list[ReadQuotaResponse]](
        status=StatusEnum.SUCCESS, data=response_data
    )
