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
from modules.web_server.schemas.response import ResponseSchema, StatusEnum


class UpdateGoogleRequest(BaseModel):
    root_folder_id: str
    profile_folder_id: str


class GetGoogleResponse(BaseModel):
    root_folder_id: Optional[str] = None
    profile_folder_id: Optional[str] = None


router = APIRouter(prefix="/integrations", tags=["Integration"])


def create_spreadsheet_if_not_exist(
    parent_folder_id: str,
    spreadsheet_name: str,
    sheet_titles: list[str],
    drive_service: Resource,
    sheets_service: Resource,
) -> str:
    spreadsheet_mime_type = "application/vnd.google-apps.spreadsheet"
    result = (
        drive_service.files()
        .list(
            q=f"'{parent_folder_id}' in parents and name = '{spreadsheet_name}' and mimeType='{spreadsheet_mime_type}'",
            fields="files(id, name)",
        )
        .execute()
    )
    files = result.get("files", [])
    if len(files) == 0:
        file_metadata = {
            "name": spreadsheet_name,
            "mimeType": spreadsheet_mime_type,
            "parents": [parent_folder_id],
        }
        file = (
            drive_service.files()
            .create(body=file_metadata, fields="id, name")
            .execute()
        )
        spreadsheet_id = file["id"]
    elif len(files) == 1:
        spreadsheet_id = files[0]["id"]
    elif len(files) > 1:
        raise Exception(f"Multiple spreadsheets named `{spreadsheet_name}` detected.")

    current_spreadsheet = (
        sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    )
    current_sheets = current_spreadsheet.get("sheets", [])
    current_sheet_title_set = set(
        sheet["properties"]["title"] for sheet in current_sheets
    )
    requests = []
    for sheet_title in sheet_titles:
        if not sheet_title in current_sheet_title_set:
            requests.append(
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_title,
                        }
                    }
                }
            )
    batch_update_spreadsheet_response = (
        sheets_service.spreadsheets()
        .batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        )
        .execute()
    )
    return spreadsheet_id


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
    drive_service: Resource = Depends(get_drive_v3_service),
    sheets_service: Resource = Depends(get_sheets_v4_service),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    profile_folder_id = update_google.profile_folder_id
    treasury_spreadsheet_id = create_spreadsheet_if_not_exist(
        parent_folder_id=profile_folder_id,
        spreadsheet_name="treasury",
        sheet_titles=["account"],
        drive_service=drive_service,
        sheets_service=sheets_service,
    )
    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_collection.update_one(
        filter={"reference": current_end_user["reference"]},
        update={
            "$set": {
                "is_onboarded": True,
                "root_folder_id": update_google.root_folder_id,
                "profile_folder_id": profile_folder_id,
                "treasury_spreadsheet_id": treasury_spreadsheet_id,
            }
        },
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
