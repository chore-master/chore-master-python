from fastapi import APIRouter, Depends

from chore_master_api.web_server.dependencies.auth import get_current_end_user
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/end_users", tags=["End User"])


@router.get("/me", response_model=ResponseSchema[dict])
async def get_me(current_end_user: dict = Depends(get_current_end_user)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "email": current_end_user["email"],
            "is_onboarded": current_end_user.get("is_onboarded", False),
        },
    )
