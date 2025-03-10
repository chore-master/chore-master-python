from datetime import datetime

from apps.chore_master_api.end_user_space.models.base import Entity


class User(Entity):
    name: str
    username: str
    password: str


class UserSession(Entity):
    user_reference: str
    user_agent: str
    is_active: bool
    expired_time: datetime
    deactivated_time: datetime
