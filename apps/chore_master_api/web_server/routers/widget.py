from fastapi import APIRouter

from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.get("/sankey", response_model=ResponseSchema[dict])
async def get_sankey():
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "nodes": [{"name": "a"}, {"name": "b"}],
            "links": [{"source": "a", "target": "b", "value": 1}],
        },
    )
