from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select, update

from apps.chore_master_api.end_user_space.models.identity import UserSession
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from modules.utils.string_utils import StringUtils


async def get_is_turnstile_token_valid(
    verify_url: str, secret_key: str, token: str
) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            verify_url,
            data={
                "secret": secret_key,
                "response": token,
            },
        )
        result = response.json()
        return result.get("success", False)


async def login_user(
    identity_uow: IdentitySQLAlchemyUnitOfWork,
    user_reference: str,
    user_agent: str,
) -> tuple[str, timedelta]:
    utc_now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    statement = select(UserSession).filter(
        UserSession.user_reference == user_reference,
        UserSession.is_active == True,
        UserSession.expired_time > utc_now,
    )
    result = await identity_uow.session.execute(statement)
    active_user_session = result.scalars().unique().first()

    statement = (
        update(UserSession)
        .filter(
            UserSession.user_reference == user_reference,
            UserSession.expired_time < utc_now,
        )
        .values(
            is_active=False,
            deactivated_time=utc_now,
        )
    )
    await identity_uow.session.execute(statement)

    if active_user_session is None:
        user_session_reference = StringUtils.new_short_id(length=8)
        user_session_ttl = timedelta(days=14)
        await identity_uow.user_session_repository.insert_one(
            UserSession(
                reference=user_session_reference,
                user_reference=user_reference,
                user_agent=user_agent,
                is_active=True,
                expired_time=utc_now + user_session_ttl,
            )
        )
    else:
        user_session_reference = active_user_session.reference
        user_session_ttl = active_user_session.expired_time - utc_now
