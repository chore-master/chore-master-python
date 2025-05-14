from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, Response
from pydantic import BaseModel
from sqlalchemy import select, update

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.end_user_space.models.identity import UserSession
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.service_layers.auth import (
    get_is_turnstile_token_valid,
    login_user,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_identity_uow
from apps.chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.utils.string_utils import StringUtils
from modules.web_server.exceptions import UnauthenticatedError, UnauthorizedError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str
    turnstile_token: str


@router.post("/user_sessions/login")
async def post_user_sessions_login(
    login_request: LoginRequest,
    response: Response,
    user_agent: Optional[str] = Header(default=None),
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
    identity_uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
):
    is_turnstile_token_valid = await get_is_turnstile_token_valid(
        verify_url=chore_master_api_web_server_config.CLOUDFLARE_TURNSTILE_VERIFY_URL,
        secret_key=chore_master_api_web_server_config.CLOUDFLARE_TURNSTILE_SECRET_KEY,
        token=login_request.turnstile_token,
    )
    if not is_turnstile_token_valid:
        raise UnauthorizedError("Forbidden")

    async with identity_uow:
        users = await identity_uow.user_repository.find_many(
            filter={
                "username": login_request.username,
                "password": login_request.password,
            },
            limit=1,
        )
        user = next(iter(users), None)
        if user is None:
            raise UnauthenticatedError("Invalid username or password")
        else:
            user_reference = user.reference

        user_session_reference, user_session_ttl = await login_user(
            identity_uow=identity_uow,
            user_reference=user_reference,
            user_agent=user_agent,
        )
        await identity_uow.commit()

    response.set_cookie(
        key=chore_master_api_web_server_config.SESSION_COOKIE_KEY,
        value=user_session_reference,
        domain=chore_master_api_web_server_config.SESSION_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
        max_age=user_session_ttl.total_seconds(),
    )
    return ResponseSchema[None](status=StatusEnum.SUCCESS, data=None)


@router.post("/user_sessions/logout")
async def post_user_sessions_logout(
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
