from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Cookie, Depends, Header, Response

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.dependencies.database import get_chore_master_api_db
from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from chore_master_api.web_server.schemas.request import EndUserLoginSchema
from modules.database.mongo_client import MongoDB
from modules.web_server.exceptions import UnauthenticatedError
from modules.web_server.schemas.response import ResponseSchema, StatusEnum

router = APIRouter(prefix="/end_users", tags=["End Users"])


@router.post("/login", response_model=ResponseSchema[None])
async def post_login(
    end_user_login: EndUserLoginSchema,
    response: Response,
    user_agent: Optional[str] = Header(default=None),
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    end_user_collection = chore_master_api_db.get_collection("end_user")
    end_user_session_collection = chore_master_api_db.get_collection("end_user_session")
    end_user = end_user_collection.find_one(
        {"email": end_user_login.email, "password": end_user_login.password}
    )
    if end_user is None:
        raise UnauthenticatedError()
    end_user_reference = end_user["reference"]
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    active_end_user_session = end_user_session_collection.find_one(
        {
            "end_user_reference": end_user_reference,
            "is_active": True,
            "expired_time": {"$gt": utc_now},
        }
    )
    end_user_session_collection.update_many(
        {
            "end_user_reference": end_user_reference,
            "expired_time": {"$lt": utc_now},
        },
        {
            "$set": {
                "is_active": False,
                "deactivated_time": utc_now,
            }
        },
    )
    if active_end_user_session is None:
        end_user_session_reference = uuid4()
        session_ttl = timedelta(days=14)
        session_dict = {
            "reference": end_user_session_reference,
            "end_user_reference": end_user_reference,
            "user_agent": user_agent,
            "is_active": True,
            "expired_time": utc_now + session_ttl,
            "created_time": utc_now,
            "deactivated_time": None,
        }
        end_user_session_collection.insert_one(session_dict)
    else:
        end_user_session_reference = active_end_user_session["reference"]
        session_ttl = (
            active_end_user_session["expired_time"].replace(tzinfo=timezone.utc)
            - utc_now
        )

    response.set_cookie(
        key="end_user_session_reference",
        value=str(end_user_session_reference),
        domain=chore_master_api_web_server_config.END_USER_AUTH_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
        max_age=session_ttl.total_seconds(),
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )


@router.get("/logout", response_model=ResponseSchema[None])
async def get_logout(
    response: Response,
    end_user_session_reference: Annotated[
        Optional[UUID], Cookie(alias="end_user_session_reference")
    ] = None,
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
    chore_master_api_db: MongoDB = Depends(get_chore_master_api_db),
):
    end_user_session_collection = chore_master_api_db.get_collection("end_user_session")
    if end_user_session_reference is not None:
        end_user_session_collection.find_one_and_update(
            {"reference": end_user_session_reference}, {"$set": {"is_active": False}}
        )
    response.delete_cookie(
        "end_user_session_reference",
        domain=chore_master_api_web_server_config.END_USER_AUTH_COOKIE_DOMAIN,
        httponly=True,
        samesite="lax",
    )
    return ResponseSchema[None](
        status=StatusEnum.SUCCESS,
        data=None,
    )
