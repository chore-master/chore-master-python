from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, RootModel

from chore_master_api.logical_sheets.some_entity import some_entity_logical_sheet
from chore_master_api.web_server.dependencies.auth import get_current_end_user
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.dependencies.google_service import get_google_service
from modules.database.mongo_client import MongoDB
from modules.google_service.google_service import GoogleService
from modules.web_server.schemas.response import ResponseSchema, StatusEnum


class UpdateGoogleRequest(BaseModel):
    drive_root_folder_id: str


class GetGoogleResponse(RootModel):
    root: Optional[dict] = None


router = APIRouter(prefix="/integrations", tags=["Integration"])


@router.get("/google", response_model=ResponseSchema[GetGoogleResponse])
async def get_google(current_end_user: dict = Depends(get_current_end_user)):
    return ResponseSchema[GetGoogleResponse](
        status=StatusEnum.SUCCESS,
        data=GetGoogleResponse(current_end_user.get("google")),
    )


@router.patch("/google", response_model=ResponseSchema[None])
async def patch_google(
    update_google: UpdateGoogleRequest,
    current_end_user: dict = Depends(get_current_end_user),
    google_service: GoogleService = Depends(get_google_service),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    some_entity_spreadsheet_file_dict = google_service.migrate_spreadsheet_file(
        parent_folder_id=update_google.drive_root_folder_id,
        spreadsheet_name="some_entity",
    )
    some_entity_spreadsheet_id = some_entity_spreadsheet_file_dict["id"]
    google_service.migrate_logical_sheet(
        some_entity_spreadsheet_id, some_entity_logical_sheet
    )
    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_collection.update_one(
        filter={"reference": current_end_user["reference"]},
        update={
            "$set": {
                "is_mounted": True,
                "google": {
                    "drive": {
                        "root_folder_id": update_google.drive_root_folder_id,
                    },
                    "spreadsheet": {
                        "some_entity_spreadsheet_id": some_entity_spreadsheet_id,
                    },
                },
            }
        },
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
