from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, RootModel

from chore_master_api.logical_sheets.some_module.some_entity import (
    some_entity_logical_sheet,
)
from chore_master_api.web_server.dependencies.auth import get_current_end_user
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.dependencies.google_service import get_google_service
from modules.database.mongo_client import MongoDB
from modules.google_service.google_service import GoogleService
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/account_center", tags=["Account Center"])


class UpdateIntegrationGoogleRequest(BaseModel):
    drive_root_folder_id: str


class GetIntegrationGoogleResponse(RootModel):
    root: Optional[dict] = None


@router.get("/end_users/me", response_model=ResponseSchema[dict])
async def get_end_users_me(current_end_user: dict = Depends(get_current_end_user)):
    return ResponseSchema[dict](
        status=StatusEnum.SUCCESS,
        data={
            "email": current_end_user["email"],
            "is_mounted": current_end_user.get("is_mounted", False),
        },
    )


@router.get(
    "/integrations/google", response_model=ResponseSchema[GetIntegrationGoogleResponse]
)
async def get_integrations_google(
    current_end_user: dict = Depends(get_current_end_user),
):
    return ResponseSchema[GetIntegrationGoogleResponse](
        status=StatusEnum.SUCCESS,
        data=GetIntegrationGoogleResponse(current_end_user.get("google")),
    )


@router.patch("/integrations/google", response_model=ResponseSchema[None])
async def patch_integrations_google(
    update_google: UpdateIntegrationGoogleRequest,
    current_end_user: dict = Depends(get_current_end_user),
    google_service: GoogleService = Depends(get_google_service),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    some_module_spreadsheet_file_dict = google_service.migrate_spreadsheet_file(
        parent_folder_id=update_google.drive_root_folder_id,
        spreadsheet_name="some_module",
    )
    some_module_spreadsheet_id = some_module_spreadsheet_file_dict["id"]
    google_service.migrate_logical_sheet(
        some_module_spreadsheet_id, some_entity_logical_sheet
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
                        "some_module_spreadsheet_id": some_module_spreadsheet_id,
                    },
                },
            }
        },
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )