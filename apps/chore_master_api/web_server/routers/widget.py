from fastapi import APIRouter

from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.get("/sankey")
async def get_sankey():
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "nodes": [
                {"id": "A"},
                {"id": "B"},
                {"id": "C"},
                {"id": "D"},
                {"id": "E"},
                {"id": "F"},
            ],
            "links": [
                {"source": "A", "target": "B", "value": 10},
                {"source": "A", "target": "C", "value": 20},
                {"source": "B", "target": "D", "value": 30},
                {"source": "C", "target": "D", "value": 40},
                {"source": "E", "target": "F", "value": 2},
            ],
        },
    )
