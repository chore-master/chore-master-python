from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.identity.role import (
    router as role_router,
)
from apps.chore_master_api.web_server.routers.v1.identity.user import (
    router as user_router,
)
from apps.chore_master_api.web_server.routers.v1.identity.user_session import (
    router as user_session_router,
)

router = APIRouter(prefix="/identity", tags=["Identity"])

router.include_router(user_router)
router.include_router(user_session_router)
router.include_router(role_router)
