from fastapi import APIRouter, Depends
from googleapiclient.discovery import Resource

from chore_master_api.web_server.dependencies.auth import get_current_end_user
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.dependencies.google_service import (
    get_drive_v3_service,
    get_sheets_v4_service,
)
from modules.database.mongo_client import MongoDB
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/integrations", tags=["Integration"])


@router.post("/google/initialize", response_model=ResponseSchema[dict])
async def post_google_initialize(
    drive_service: Resource = Depends(get_drive_v3_service),
    current_end_user: dict = Depends(get_current_end_user),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    file_metadata = {
        "name": ".chore_master",
        "mimeType": "application/vnd.google-apps.folder",
    }
    result = (
        drive_service.files()
        .list(
            q=f"name = '{file_metadata['name']}' and mimeType='{file_metadata['mimeType']}'",
            fields="files(id, name)",
        )
        .execute()
    )
    files = result.get("files", [])
    if len(files) == 0:
        file = drive_service.files().create(body=file_metadata, fields="id").execute()
    elif len(files) == 1:
        file = files[0]
    elif len(files) > 1:
        raise BadRequestError("Multiple folders named `.chore_master` detected.")

    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_collection.update_one(
        filter={"reference": current_end_user["reference"]},
        update={"$set": {"root_folder_id": file["id"]}},
    )
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data=file,
    )
