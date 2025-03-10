from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.identity.user_session import (
    router as user_session_router,
)

router = APIRouter(prefix="/identity", tags=["Identity"])

router.include_router(user_session_router)
