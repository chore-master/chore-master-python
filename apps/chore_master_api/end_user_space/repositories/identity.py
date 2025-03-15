from typing import Type

from apps.chore_master_api.end_user_space.models.identity import (
    User,
    UserRole,
    UserSession,
)
from modules.repositories.base_sqlalchemy_repository import BaseSQLAlchemyRepository


class UserRepository(BaseSQLAlchemyRepository[User]):
    @property
    def entity_class(self) -> Type[User]:
        return User


class UserSessionRepository(BaseSQLAlchemyRepository[UserSession]):
    @property
    def entity_class(self) -> Type[UserSession]:
        return UserSession


class UserRoleRepository(BaseSQLAlchemyRepository[UserRole]):
    @property
    def entity_class(self) -> Type[UserRole]:
        return UserRole
