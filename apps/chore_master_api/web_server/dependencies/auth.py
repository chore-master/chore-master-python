from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends

from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_api_db,
)
from modules.database.mongo_client import MongoDB
from modules.web_server.exceptions import UnauthenticatedError, UnauthorizedError


async def get_current_end_user_session(
    end_user_session_reference: Annotated[
        Optional[str], Cookie(alias="end_user_session_reference")
    ] = None,
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
) -> dict:
    if end_user_session_reference is None:
        raise UnauthenticatedError("current request is not authenticated")
    end_user_session_collection = chore_master_api_db.get_collection("end_user_session")
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    current_end_user_session = await anext(
        end_user_session_collection.aggregate(
            pipeline=[
                {
                    "$match": {
                        # "reference": UUID(end_user_session_reference),
                        "reference": end_user_session_reference,
                        "is_active": True,
                        "expired_time": {"$gt": utc_now},
                    }
                },
                {
                    "$limit": 1,
                },
                {
                    "$lookup": {
                        "localField": "end_user_reference",
                        "from": "end_user",
                        "foreignField": "reference",
                        "as": "end_users",
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "end_users._id": 0,
                    }
                },
            ]
        ),
        None,
    )
    if current_end_user_session is None:
        raise UnauthorizedError("current request is not authorized")
    return current_end_user_session


async def get_current_end_user(
    current_end_user_session: dict = Depends(get_current_end_user_session),
) -> dict:
    current_end_user = current_end_user_session["end_users"][0]
    return current_end_user
