from typing import Type

from apps.chore_master_api.end_user_space.models.identity import (
    Role,
    User,
    UserAttribute,
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


class RoleRepository(BaseSQLAlchemyRepository[Role]):
    @property
    def entity_class(self) -> Type[Role]:
        return Role


class UserAttributeRepository(BaseSQLAlchemyRepository[UserAttribute]):
    @property
    def entity_class(self) -> Type[UserAttribute]:
        return UserAttribute
