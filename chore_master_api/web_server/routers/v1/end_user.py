from fastapi import APIRouter

from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/end_users", tags=["End Users"])


@router.get("/test", response_model=ResponseSchema[None])
async def get_test():
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
