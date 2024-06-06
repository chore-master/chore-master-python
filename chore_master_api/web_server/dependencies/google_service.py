from fastapi import Depends
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.dependencies.auth import get_current_end_user_session
from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.google_service.google_service import GoogleService
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


async def get_google_service(
    credentials: Credentials = Depends(get_credentials),
) -> GoogleService:
    return GoogleService(credentials=credentials)
