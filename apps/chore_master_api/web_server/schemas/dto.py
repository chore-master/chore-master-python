from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OffsetPagination(BaseModel):
    offset: int
    limit: int
    is_from_request: bool


class TimeCursorPagination(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int
    is_from_request: bool
