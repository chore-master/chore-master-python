import os

from fastapi import APIRouter
from pydantic import BaseModel

from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/infra", tags=["Infra"])


class GetUserDatabaseRevisionsResponse(BaseModel):
    file_names: list[str]


@router.get("/user_database/revisions")
async def get_user_database_revisions():
    directory_path = "./apps/chore_master_api/end_user_space/migrations"
    if os.path.isdir(directory_path):
        file_names = [
            f
            for f in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, f))
        ]
    else:
        file_names = []
    return ResponseSchema[GetUserDatabaseRevisionsResponse](
        status=StatusEnum.SUCCESS,
        data=GetUserDatabaseRevisionsResponse(file_names=file_names),
    )
