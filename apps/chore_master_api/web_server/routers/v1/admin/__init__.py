from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.admin.database import (
    router as database_router,
)
from apps.chore_master_api.web_server.routers.v1.admin.quota import (
    router as quota_router,
)
from apps.chore_master_api.web_server.routers.v1.admin.user import router as user_router
from apps.chore_master_api.web_server.routers.v1.admin.user_role import (
    router as user_role_router,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(database_router)
router.include_router(user_router)
router.include_router(user_role_router)
router.include_router(quota_router)
