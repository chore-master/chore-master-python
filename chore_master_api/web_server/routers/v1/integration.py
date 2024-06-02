from typing import Optional

from fastapi import APIRouter, Depends
from googleapiclient.discovery import Resource
from pydantic import BaseModel

from chore_master_api.web_server.dependencies.auth import get_current_end_user
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.dependencies.google_service import (
    get_drive_v3_service,
    get_sheets_v4_service,
)
from modules.database.mongo_client import MongoDB
from modules.web_server.exceptions import BadRequestError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum


class UpdateGoogleRequest(BaseModel):
    root_folder_id: str
    profile_folder_id: str


class GetGoogleResponse(BaseModel):
    root_folder_id: Optional[str] = None
    profile_folder_id: Optional[str] = None


router = APIRouter(prefix="/integrations", tags=["Integration"])


# @router.post("/google/initialize", response_model=ResponseSchema[dict])
# async def post_google_initialize(
#     drive_service: Resource = Depends(get_drive_v3_service),
#     current_end_user: dict = Depends(get_current_end_user),
#     chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
# ):
#     file_metadata = {
#         "name": ".chore_master",
#         "mimeType": "application/vnd.google-apps.folder",
#     }
#     result = (
#         drive_service.files()
#         .list(
#             q=f"name = '{file_metadata['name']}' and mimeType='{file_metadata['mimeType']}'",
#             fields="files(id, name)",
#         )
#         .execute()
#     )
#     files = result.get("files", [])
#     if len(files) == 0:
#         file = drive_service.files().create(body=file_metadata, fields="id").execute()
#     elif len(files) == 1:
#         file = files[0]
#     elif len(files) > 1:
#         raise BadRequestError("Multiple folders named `.chore_master` detected.")

#     end_user_collection = chore_master_api_db.get_collection("end_user")
#     end_user_collection.update_one(
#         filter={"reference": current_end_user["reference"]},
#         update={"$set": {"root_folder_id": file["id"]}},
#     )
#     return ResponseSchema[dict](
#         status=StatusEnum.SUCCESS,
#         data=file,
#     )


@router.get("/google", response_model=ResponseSchema[GetGoogleResponse])
async def get_google(current_end_user: dict = Depends(get_current_end_user)):
    return ResponseSchema[GetGoogleResponse](
        status=StatusEnum.SUCCESS,
        data=GetGoogleResponse(
            root_folder_id=current_end_user.get("root_folder_id"),
            profile_folder_id=current_end_user.get("profile_folder_id"),
        ),
    )


@router.patch("/google", response_model=ResponseSchema[None])
async def patch_google(
    update_google: UpdateGoogleRequest,
    current_end_user: dict = Depends(get_current_end_user),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_collection.update_one(
        filter={"reference": current_end_user["reference"]},
        update={
            "$set": {
                "is_onboarded": True,
                "root_folder_id": update_google.root_folder_id,
                "profile_folder_id": update_google.profile_folder_id,
            }
        },
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


# @router.post("/google/profiles", response_model=ResponseSchema[list])
# async def get_google_profiles(
#     drive_service: Resource = Depends(get_drive_v3_service),
#     current_end_user: dict = Depends(get_current_end_user),
# ):
#     root_folder_id = current_end_user.get("root_folder_id")
#     result = (
#         drive_service.files()
#         .list(
#             q=f"'{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
#             fields="files(id, name)",
#         )
#         .execute()
#     )
#     files = result.get("files", [])
#     profile_files = [f["name"].startswith("profile_") for f in files]
#     return ResponseSchema[dict](
#         status=StatusEnum.SUCCESS,
#         data=profile_files,
#     )
