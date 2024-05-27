import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from urllib.parse import urlencode, urljoin
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from chore_master_api.web_server.schemas.request import (
    EndUserLoginSchema,
    EndUserRegisterSchema,
)
from modules.database.mongo_client import MongoDB
from modules.web_server.exceptions import BadRequestError, UnauthenticatedError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/auth", tags=["Auth"])


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
        "scope": " ".join(
            [
                # https://developers.google.com/identity/protocols/oauth2/scopes?hl=zh-tw
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/spreadsheets",
            ]
        ),
        "state": json.dumps({"next_uri": next_uri}),
    }
    url = f"{auth_endpoint}?{urlencode(query_params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def get_google_callback(
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
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
    # unverified_header = jwt.get_unverified_header(id_token)
    # kid = unverified_header["kid"]

    jwks_client = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)

    # jwks_res = await client.get("https://www.googleapis.com/oauth2/v3/certs")
    # jwks_dict = jwks_res.json()
    # public_key = jwt.PyJWKClient.match_kid(jwks_dict["keys"], kid)

    # public_key = next(
    #     jwt.algorithms.RSAAlgorithm.from_jwk(key)
    #     for key in jwks_dict["keys"]
    #     if key["kid"] == kid
    # )
    # jwt.decode_complete(
    #     id_token,
    #     key=signing_key.key,
    #     algorithms=signing_algos,
    #     audience=client_id,
    # )

    payload = jwt.decode(
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
    return RedirectResponse(next_uri)
