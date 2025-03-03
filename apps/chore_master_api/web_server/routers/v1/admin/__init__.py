from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.admin.auth import router as auth_router
from apps.chore_master_api.web_server.routers.v1.admin.database import (
    router as database_router,
)
from apps.chore_master_api.web_server.routers.v1.admin.end_user import (
    router as end_user_router,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(auth_router)
router.include_router(end_user_router)
router.include_router(database_router)
