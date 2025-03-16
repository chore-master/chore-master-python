from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Query

from apps.chore_master_api.web_server.schemas.dto import (
    OffsetPagination,
    TimeCursorPagination,
)
from modules.web_server.exceptions import BadRequestError


async def get_offset_pagination(
    offset: Annotated[Optional[int], Query()] = None,
    limit: Annotated[Optional[int], Query()] = None,
) -> OffsetPagination:
    is_from_request = offset is None
    if offset is None:
        offset = 0
    if limit is None:
        limit = 100
    elif limit <= 0 or 100 < limit:
        raise BadRequestError("`limit` should belong to [1, 100]")
    return OffsetPagination(offset=offset, limit=limit, is_from_request=is_from_request)


async def get_time_cursor_pagination(
    start_time: Annotated[Optional[datetime], Query()] = None,
    end_time: Annotated[Optional[datetime], Query()] = None,
    limit: Annotated[Optional[int], Query()] = None,
) -> TimeCursorPagination:
    if start_time is not None and end_time is not None:
        raise BadRequestError("`start_time` and `end_time` are mutually exclusive")
    is_from_request = start_time is not None or end_time is not None
    if start_time is None and end_time is None:
        end_time = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    if limit is None:
        limit = 100
    elif limit <= 0 or 100 < limit:
        raise BadRequestError("`limit` should belong to [1, 100]")
    return TimeCursorPagination(
        start_time=None if start_time is None else start_time.replace(tzinfo=None),
        end_time=None if end_time is None else end_time.replace(tzinfo=None),
        limit=limit,
        is_from_request=is_from_request,
    )
