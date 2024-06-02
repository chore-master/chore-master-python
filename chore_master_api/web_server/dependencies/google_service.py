from fastapi import Depends
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.dependencies.auth import get_current_end_user_session
from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)


async def get_drive_v3_service(
    current_end_user_session: dict = Depends(get_current_end_user_session),
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
) -> Resource:
    API_SERVICE_NAME = "drive"
    API_VERSION = "v3"
    credentials = Credentials(
        token=current_end_user_session["google"]["access_token_dict"]["access_token"],
        refresh_token=current_end_user_session["google"]["refresh_token"],
        token_uri=chore_master_api_web_server_config.GOOGLE_OAUTH_TOKEN_URI,
        client_id=chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=chore_master_api_web_server_config.GOOGLE_OAUTH_SECRET,
    )
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    return service


async def get_sheets_v4_service(
    current_end_user_session: dict = Depends(get_current_end_user_session),
) -> Resource:
    API_SERVICE_NAME = "sheets"
    API_VERSION = "v4"
    credentials = Credentials(
        token=current_end_user_session["google"]["access_token_dict"]["access_token"]
    )
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    return service
