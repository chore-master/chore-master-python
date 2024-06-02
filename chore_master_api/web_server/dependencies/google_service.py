from fastapi import Depends
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.dependencies.auth import get_current_end_user_session
from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.web_server.exceptions import InternalServerError


async def get_credentials(
    current_end_user_session: dict = Depends(get_current_end_user_session),
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
) -> Credentials:
    credentials = Credentials(
        token=current_end_user_session["google"]["access_token_dict"]["access_token"],
        refresh_token=current_end_user_session["google"]["refresh_token"],
        token_uri=chore_master_api_web_server_config.GOOGLE_OAUTH_TOKEN_URI,
        client_id=chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=chore_master_api_web_server_config.GOOGLE_OAUTH_SECRET,
    )
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except HttpError as err:
            raise InternalServerError()
    return credentials


async def get_drive_v3_service(
    credentials: Credentials = Depends(get_credentials),
) -> Resource:
    # https://developers.google.com/drive/api/guides/about-files
    service = build(serviceName="drive", version="v3", credentials=credentials)
    return service


async def get_sheets_v4_service(
    credentials: Credentials = Depends(get_credentials),
) -> Resource:
    # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets
    service = build(serviceName="sheets", version="v4", credentials=credentials)
    return service
