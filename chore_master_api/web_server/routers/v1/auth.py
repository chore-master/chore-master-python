import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from urllib.parse import urlencode
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, Header, Query, Response
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.database.mongo_client import MongoDB
from modules.web_server.exceptions import UnauthenticatedError, UnauthorizedError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/auth", tags=["Auth"])

required_google_scopes = [
    # https://developers.google.com/identity/protocols/oauth2/scopes?hl=zh-tw
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


@router.get("/google/authorize")
async def get_google_authorize(
    next_uri: Annotated[str, Query()],
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
):
    auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    query_params = {
        "client_id": chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": f"{chore_master_api_web_server_config.HOST}/v1/auth/google/callback",
        "response_type": "code",
        "scope": " ".join(required_google_scopes),
        "state": json.dumps({"next_uri": next_uri}),
    }
    url = f"{auth_endpoint}?{urlencode(query_params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def get_google_callback(
    response: Response,
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    user_agent: Optional[str] = Header(default=None),
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    state_dict = json.loads(state)
    next_uri = state_dict["next_uri"]
    async with AsyncClient(timeout=None) as client:
        access_token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            json={
                "code": code,
                "client_id": chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": chore_master_api_web_server_config.GOOGLE_OAUTH_SECRET,
                "redirect_uri": f"{chore_master_api_web_server_config.HOST}/v1/auth/google/callback",
                "grant_type": "authorization_code",
            },
        )
        access_token_dict = access_token_res.json()
        """
        {
            "access_token": "ya29.a0AXooCguwead03rT46dOqC2orZmtjlSqXuDz0lQyAcp3bYbL54cJgTFAam9A1YjzCNlExmI3V19zlzlNPIRtwrELkZkI-eeapqXgBlE7ptyXXCQpl9-wPapAHsGV6j4Sblu8NqEARoagQ8HqfQFxhvicdf2SwCczglkHyaCgYKAccSARMSFQHGX2MiMfXRWa91PQ-_b1nDU74whA0171",
            "expires_in": 3599,
            "refresh_token": "1//0e89EEaRuKn5gCgYIARAAGA4SNwF-L9IrOxh_YGncGNjvVuFh9MIGoJAQOCYJaqa-TFSR7o1m2M3pE_1oqb_Q_owCtgOuugyJnL4",
            "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/drive.file",
            "token_type": "Bearer",
            "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjY3MTk2NzgzNTFhNWZhZWRjMmU3MDI3NGJiZWE2MmRhMmE4YzRhMTIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyODg1MjczMzg1Nzcta2ttbGh1NjZra2R1Ym4zcnBnZzA2MTFzdmN0czFoODEuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIyODg1MjczMzg1Nzcta2ttbGh1NjZra2R1Ym4zcnBnZzA2MTFzdmN0czFoODEuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDQ0MjQzMDgwMTA2MzU1NDY5NTAiLCJlbWFpbCI6ImdvY3JlYXRpbmdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hhc2giOiJkX0VzRXVXYU5BS3lTNGpmMU9BRDVnIiwibmFtZSI6IkNQIFdlbmciLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSXUxYTA0Z29sOE1NSFFOUWtWVTVya2o1aDJjLUpMN1EzcjBfME9IdURxXzltUjlYU209czk2LWMiLCJnaXZlbl9uYW1lIjoiQ1AiLCJmYW1pbHlfbmFtZSI6IldlbmciLCJpYXQiOjE3MTY4Mjc2NTUsImV4cCI6MTcxNjgzMTI1NX0.RKstHCi5qpieiEK56VE7Y5a_YmW8nkx1v_9d5UKu6kAXf6gCjOo3kweUKICTUwKR-0dHq9M3T55HdxHioCBJH4jouHFWl9zNn8YNacddhF9EdEBY5-x_ECCFHK4jS7eAspZW5nabyU_pzBmVDmIRuwojhb-leJK1NFIcJg8YHjIX9L0gSIxEt-0ix9b6dBfPJSuDNy1tggM2Glwg2EKK8bIlOSwZZeL8srzRxtZvWrIZyUBXv8ei6_HoWAvBk53MLr3PLCTsvnn6ABoydw032eqK4wyjGk8l2NhzuybzE8r7ObzaB9ne2d9oxA-QNucUlZKnUaP7JWWP98__a6pwoQ"
        }
        """

    id_token = access_token_dict["id_token"]
    jwks_client = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)
    google_user_dict = jwt.decode(
        id_token,
        key=signing_key.key,
        algorithms=["RS256"],
        audience=chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
    )
    """
    {
        "iss": "https://accounts.google.com",
        "azp": "288527338577-kkmlhu66kkdubn3rpgg0611svcts1h81.apps.googleusercontent.com",
        "aud": "288527338577-kkmlhu66kkdubn3rpgg0611svcts1h81.apps.googleusercontent.com",
        "sub": "104424308010635546950",
        "email": "gocreating@gmail.com",
        "email_verified": true,
        "at_hash": "bcDnsMZZk8M1i6kQu6EbAA",
        "name": "CP Weng",
        "picture": "https://lh3.googleusercontent.com/a/ACg8ocIu1a04gol8MMHQNQkVU5rkj5h2c-JL7Q3r0_0OHuDq_9mR9XSm=s96-c",
        "given_name": "CP",
        "family_name": "Weng",
        "iat": 1716830341,
        "exp": 1716833941
    }
    """

    if google_user_dict["email_verified"] is False:
        raise UnauthenticatedError("Email not verified")
    if set(access_token_dict["scope"].split(" ")) < set(required_google_scopes):
        raise UnauthorizedError("Required scopes are not granted")

    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_session_collection = chore_master_api_db.get_collection("end_user_session")
    end_user = end_user_collection.find_one({"email": google_user_dict["email"]})
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)

    if end_user is None:
        end_user_reference = uuid4()
        end_user_dict = {
            "reference": end_user_reference,
            "created_time": utc_now,
            "email": google_user_dict["email"],
        }
        end_user_collection.insert_one(end_user_dict)
    else:
        end_user_reference = end_user["reference"]

    active_end_user_session = end_user_session_collection.find_one(
        {
            "end_user_reference": end_user_reference,
            "is_active": True,
            "expired_time": {"$gt": utc_now},
        }
    )
    end_user_session_collection.update_many(
        {
            "end_user_reference": end_user_reference,
            "expired_time": {"$lt": utc_now},
        },
        {
            "$set": {
                "is_active": False,
                "deactivated_time": utc_now,
            }
        },
    )
    if active_end_user_session is None:
        end_user_session_reference = uuid4()
        end_user_session_ttl = timedelta(days=14)
        end_user_session_dict = {
            "reference": end_user_session_reference,
            "end_user_reference": end_user_reference,
            "user_agent": user_agent,
            "is_active": True,
            "expired_time": utc_now + end_user_session_ttl,
            "created_time": utc_now,
            "deactivated_time": None,
        }
        end_user_session_collection.insert_one(end_user_session_dict)
    else:
        end_user_session_reference = active_end_user_session["reference"]
        end_user_session_ttl = (
            active_end_user_session["expired_time"].replace(tzinfo=timezone.utc)
            - utc_now
        )

    response.set_cookie(
        key=chore_master_api_web_server_config.SESSION_COOKIE_DOMAIN,
        value=str(end_user_session_reference),
        domain=chore_master_api_web_server_config.SESSION_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
        max_age=end_user_session_ttl.total_seconds(),
    )
    return RedirectResponse(next_uri)


@router.post("/logout", response_model=ResponseSchema[None])
async def post_logout(
    response: Response,
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
):
    response.delete_cookie(
        chore_master_api_web_server_config.SESSION_COOKIE_KEY,
        domain=chore_master_api_web_server_config.SESSION_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
