import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from urllib.parse import urlencode
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_identity_uow
from apps.chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)

router = APIRouter()


required_google_scopes = [
    # https://developers.google.com/identity/protocols/oauth2/scopes?hl=zh-tw
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    # "https://www.googleapis.com/auth/drive",
    # "https://www.googleapis.com/auth/spreadsheets",
]


@router.get("/google/authorize")
async def get_google_authorize(
    success_redirect_uri: Annotated[str, Query()],
    error_redirect_uri: Annotated[str, Query()],
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
):
    query_params = {
        "client_id": chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": f"{chore_master_api_web_server_config.API_ORIGIN}/v1/identity/google/callback",
        "response_type": "code",
        "scope": " ".join(required_google_scopes),
        "state": json.dumps(
            {
                "success_redirect_uri": success_redirect_uri,
                "error_redirect_uri": error_redirect_uri,
            }
        ),
        # https://blog.miniasp.com/post/2023/06/14/How-to-issue-Refresh-Token-in-Google-OAuth
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{chore_master_api_web_server_config.GOOGLE_OAUTH_ENDPOINT}?{urlencode(query_params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def get_google_callback(
    state: Annotated[str, Query()],
    code: Annotated[Optional[str], Query()] = None,
    user_agent: Optional[str] = Header(default=None),
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
    identity_uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    state_dict = json.loads(state)
    error_redirect_uri = state_dict["error_redirect_uri"]
    success_redirect_uri = state_dict["success_redirect_uri"]

    error_response = RedirectResponse(error_redirect_uri)
    if code is None:
        return error_response

    response = RedirectResponse(success_redirect_uri)

    async with AsyncClient(timeout=None) as client:
        access_token_res = await client.post(
            chore_master_api_web_server_config.GOOGLE_OAUTH_TOKEN_URI,
            json={
                "code": code,
                "client_id": chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": chore_master_api_web_server_config.GOOGLE_OAUTH_SECRET,
                "redirect_uri": f"{chore_master_api_web_server_config.IAM_API_ORIGIN}/v1/auth/google/callback",
                "grant_type": "authorization_code",
            },
        )
        access_token_dict = access_token_res.json()
        """
        {
            "access_token": "ya29.a0AXooCguwead03rT46dOqC2orZmtjlSqXuDz0lQyAcp3bYbL54cJgTFAam9A1YjzCNlExmI3V19zlzlNPIRtwrELkZkI-eeapqXgBlE7ptyXXCQpl9-wPapAHsGV6j4Sblu8NqEARoagQ8HqfQFxhvicdf2SwCczglkHyaCgYKAccSARMSFQHGX2MiMfXRWa91PQ-_b1nDU74whA0171",
            "expires_in": 3599,
            "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/drive.file",
            "token_type": "Bearer",
            "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjY3MTk2NzgzNTFhNWZhZWRjMmU3MDI3NGJiZWE2MmRhMmE4YzRhMTIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyODg1MjczMzg1Nzcta2ttbGh1NjZra2R1Ym4zcnBnZzA2MTFzdmN0czFoODEuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIyODg1MjczMzg1Nzcta2ttbGh1NjZra2R1Ym4zcnBnZzA2MTFzdmN0czFoODEuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDQ0MjQzMDgwMTA2MzU1NDY5NTAiLCJlbWFpbCI6ImdvY3JlYXRpbmdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hhc2giOiJkX0VzRXVXYU5BS3lTNGpmMU9BRDVnIiwibmFtZSI6IkNQIFdlbmciLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSXUxYTA0Z29sOE1NSFFOUWtWVTVya2o1aDJjLUpMN1EzcjBfME9IdURxXzltUjlYU209czk2LWMiLCJnaXZlbl9uYW1lIjoiQ1AiLCJmYW1pbHlfbmFtZSI6IldlbmciLCJpYXQiOjE3MTY4Mjc2NTUsImV4cCI6MTcxNjgzMTI1NX0.RKstHCi5qpieiEK56VE7Y5a_YmW8nkx1v_9d5UKu6kAXf6gCjOo3kweUKICTUwKR-0dHq9M3T55HdxHioCBJH4jouHFWl9zNn8YNacddhF9EdEBY5-x_ECCFHK4jS7eAspZW5nabyU_pzBmVDmIRuwojhb-leJK1NFIcJg8YHjIX9L0gSIxEt-0ix9b6dBfPJSuDNy1tggM2Glwg2EKK8bIlOSwZZeL8srzRxtZvWrIZyUBXv8ei6_HoWAvBk53MLr3PLCTsvnn6ABoydw032eqK4wyjGk8l2NhzuybzE8r7ObzaB9ne2d9oxA-QNucUlZKnUaP7JWWP98__a6pwoQ"
        }
        """

    id_token = access_token_dict["id_token"]
    jwks_client = jwt.PyJWKClient(
        chore_master_api_web_server_config.GOOGLE_OAUTH_JWKS_URI
    )
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)
    google_user_dict = jwt.decode(
        id_token,
        key=signing_key.key,
        algorithms=["RS256"],
        audience=chore_master_api_web_server_config.GOOGLE_OAUTH_CLIENT_ID,
        options={"verify_iat": False},
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
        return error_response
    if set(access_token_dict["scope"].split(" ")) < set(
        ["openid"] + required_google_scopes
    ):
        return error_response

    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_session_collection = chore_master_api_db.get_collection("end_user_session")
    end_user = await end_user_collection.find_one({"email": google_user_dict["email"]})
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

    active_end_user_session = await end_user_session_collection.find_one(
        {
            "end_user_reference": end_user_reference,
            "is_active": True,
            "expired_time": {"$gt": utc_now},
        }
    )
    await end_user_session_collection.update_many(
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
            "google": {
                "refresh_token": access_token_dict["refresh_token"],
                "access_token_dict": access_token_dict,
                "user_dict": google_user_dict,
            },
        }
        end_user_session_collection.insert_one(end_user_session_dict)
    else:
        end_user_session_reference = active_end_user_session["reference"]
        update_end_user_session_dict = {
            "google.access_token_dict": access_token_dict,
            "google.user_dict": google_user_dict,
        }
        if "refresh_token" in access_token_dict:
            update_end_user_session_dict["google.refresh_token"] = access_token_dict[
                "refresh_token"
            ]
        await end_user_session_collection.update_one(
            filter={"reference": end_user_session_reference},
            update={"$set": update_end_user_session_dict},
        )
        end_user_session_ttl = (
            active_end_user_session["expired_time"].replace(tzinfo=timezone.utc)
            - utc_now
        )

    response.set_cookie(
        key=chore_master_api_web_server_config.SESSION_COOKIE_KEY,
        value=str(end_user_session_reference),
        domain=chore_master_api_web_server_config.SESSION_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
        max_age=end_user_session_ttl.total_seconds(),
    )
    return response
