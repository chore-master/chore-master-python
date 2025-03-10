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
from apps.chore_master_api.web_server.dependencies.end_user_space import (
    get_identity_uow,
)
from apps.chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.utils.string_utils import StringUtils
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


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
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    async with identity_uow:
        end_users = await identity_uow.user_repository.find_many(
            filter={
                "username": login_request.username,
                "password": login_request.password,
            },
            limit=1,
        )
        end_user = next(iter(end_users), None)
        if end_user is None:
            end_user_reference = StringUtils.new_short_id(length=8)
            end_user_dict = {
                "reference": end_user_reference,
                "created_time": utc_now,
                "username": login_request.username,
                "password": login_request.password,
            }
            await identity_uow.user_repository.insert_one(end_user_dict)
        else:
            end_user_reference = end_user.reference

        statement = select(UserSession).filter(
            UserSession.user_reference == end_user_reference,
            UserSession.is_active == True,
            UserSession.expired_time > utc_now,
        )
        result = await identity_uow.session.execute(statement)
        active_end_user_session = result.scalars().unique().first()

        statement = (
            update(UserSession)
            .filter(
                UserSession.user_reference == end_user_reference,
                UserSession.expired_time < utc_now,
            )
            .values(
                is_active=False,
                deactivated_time=utc_now,
            )
        )
        await identity_uow.session.execute(statement)

        if active_end_user_session is None:
            end_user_session_reference = StringUtils.new_short_id(length=8)
            end_user_session_ttl = timedelta(days=14)
            await identity_uow.user_session_repository.insert_one(
                UserSession(
                    reference=end_user_session_reference,
                    user_reference=end_user_reference,
                    user_agent=user_agent,
                    is_active=True,
                    expired_time=utc_now + end_user_session_ttl,
                )
            )
        else:
            end_user_session_reference = active_end_user_session.reference
            end_user_session_ttl = (
                active_end_user_session.expired_time.replace(tzinfo=timezone.utc)
                - utc_now
            )
        await identity_uow.commit()

    response.set_cookie(
        key=chore_master_api_web_server_config.SESSION_COOKIE_KEY,
        value=end_user_session_reference,
        domain=chore_master_api_web_server_config.SESSION_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
        max_age=end_user_session_ttl.total_seconds(),
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
