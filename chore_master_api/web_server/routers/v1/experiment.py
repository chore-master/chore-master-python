from fastapi import APIRouter

from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/experiments", tags=["Experiment"])


@router.post("/resource", response_model=ResponseSchema[None])
async def post_resource():
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
