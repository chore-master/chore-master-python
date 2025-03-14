from datetime import datetime, timezone
from typing import Annotated, AsyncIterator, Optional

from fastapi import Cookie, Depends
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from apps.chore_master_api.end_user_space.models.identity import (
    User,
    UserRole,
    UserSession,
)
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.web_server.dependencies.unit_of_work import get_identity_uow
from modules.web_server.exceptions import UnauthenticatedError, UnauthorizedError


async def get_current_user_session(
    end_user_session_reference: Annotated[
        Optional[str], Cookie(alias="cm_end_user_session_reference")
    ] = None,
    identity_uow: IdentitySQLAlchemyUnitOfWork = Depends(get_identity_uow),
) -> AsyncIterator[UserSession]:
    if end_user_session_reference is None:
        raise UnauthenticatedError("current request is not authenticated")

    async with identity_uow:
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        statement = (
            select(UserSession)
            .where(
                UserSession.reference == end_user_session_reference,
                UserSession.expired_time > utc_now,
                UserSession.is_active == True,
                UserSession.deactivated_time == None,
            )
            .options(
                joinedload(UserSession.user).options(
                    joinedload(User.user_roles).options(joinedload(UserRole.role))
                ),
            )
        )
        result = await identity_uow.session.execute(statement)
        current_end_user_session = next(iter(result.scalars().unique().all()), None)
        if current_end_user_session is None:
            raise UnauthorizedError("current request is not authorized")
        yield current_end_user_session


async def get_current_user(
    current_user_session: UserSession = Depends(get_current_user_session),
) -> User:
    current_user = current_user_session.user
    if current_user is None:
        raise UnauthenticatedError("current request is not authenticated")
    return current_user


def require_all_roles(role_symbols: list[str]):
    async def _require_all_roles(
        current_user: User = Depends(get_current_user),
    ):
        current_user_role_symbol_set = set(
            user_role.role.symbol for user_role in current_user.user_roles
        )
        required_role_symbol_set = set(role_symbols)
        if not required_role_symbol_set.issubset(current_user_role_symbol_set):
            raise UnauthorizedError("current request is not authorized")

    return _require_all_roles


require_admin_role = require_all_roles(["ADMIN"])
