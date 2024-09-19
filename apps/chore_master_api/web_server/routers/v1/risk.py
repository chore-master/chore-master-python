from fastapi import APIRouter
from pydantic import BaseModel

from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/risk", tags=["Risk"])


class ReadAbcResponse(BaseModel):
    a: str


@router.get("/abc", response_model=ResponseSchema[ReadAbcResponse])
async def get_some_entities():
    return ResponseSchema(
        status=StatusEnum.SUCCESS, data=ReadAbcResponse(a="some string")
    )
