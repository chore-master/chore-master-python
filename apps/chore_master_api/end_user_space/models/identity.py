from datetime import datetime
from typing import Optional

from apps.chore_master_api.end_user_space.models.base import Entity


class User(Entity):
    name: str
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None


class Role(Entity):
    symbol: str


class UserRole(Entity):
    user_reference: str
    role_reference: str


class UserSession(Entity):
    user_reference: str
    user_agent: str
    is_active: bool
    expired_time: datetime
    deactivated_time: Optional[datetime] = None
