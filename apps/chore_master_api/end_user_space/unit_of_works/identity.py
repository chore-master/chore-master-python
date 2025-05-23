from __future__ import annotations

from apps.chore_master_api.end_user_space.repositories import identity
from modules.unit_of_works.base_sqlalchemy_unit_of_work import BaseSQLAlchemyUnitOfWork


class IdentitySQLAlchemyUnitOfWork(BaseSQLAlchemyUnitOfWork):
    async def __aenter__(self) -> IdentitySQLAlchemyUnitOfWork:
        await super().__aenter__()
        self.user_repository = identity.UserRepository(self.session)
        self.user_session_repository = identity.UserSessionRepository(self.session)
        self.user_role_repository = identity.UserRoleRepository(self.session)
        self.role_repository = identity.RoleRepository(self.session)
        self.user_attribute_repository = identity.UserAttributeRepository(self.session)
        return self

    async def __aexit__(self, *args):
        self.user_attribute_repository = None
        self.role_repository = None
        self.user_role_repository = None
        self.user_session_repository = None
        self.user_repository = None
        await super().__aexit__(*args)
