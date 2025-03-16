from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CurrentUser(BaseModel):
    class _UserRole(BaseModel):
        class _Role(BaseModel):
            symbol: str

        role: _Role

    reference: str
    name: str
    user_roles: list[_UserRole]


class CurrentUserSession(BaseModel):
    user: CurrentUser


class OffsetPagination(BaseModel):
    offset: int
    limit: int
    is_from_request: bool


class TimeCursorPagination(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int
    is_from_request: bool
