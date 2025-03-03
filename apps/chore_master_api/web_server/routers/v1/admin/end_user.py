from fastapi import APIRouter, Depends

from apps.chore_master_api.web_server.dependencies.auth import get_current_end_user
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


@router.get("/end_users/me")
async def get_end_users_me(current_end_user: dict = Depends(get_current_end_user)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "email": current_end_user["email"],
            # "is_mounted": current_end_user.get("is_mounted", False),
        },
    )
