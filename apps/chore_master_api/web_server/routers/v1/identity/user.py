from fastapi import APIRouter, Depends

from apps.chore_master_api.end_user_space.models.identity import User
from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


@router.get("/users/me")
async def get_users_me(current_user: User = Depends(get_current_end_user)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "name": current_user.name,
        },
    )
