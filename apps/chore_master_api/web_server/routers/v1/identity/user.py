from fastapi import APIRouter, Depends

from apps.chore_master_api.web_server.dependencies.auth import get_current_user
from apps.chore_master_api.web_server.schemas.dto import CurrentUser
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


@router.get("/users/me")
async def get_users_me(current_user: CurrentUser = Depends(get_current_user)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "name": current_user.name,
            "user_roles": [
                {
                    "role": {
                        "symbol": user_role.role.symbol,
                    }
                }
                for user_role in current_user.user_roles
            ],
        },
    )
