from fastapi import Depends
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from chore_master_api.web_server.dependencies.auth import get_current_end_user_session


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
