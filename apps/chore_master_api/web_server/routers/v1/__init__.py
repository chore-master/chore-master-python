from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.admin import router as admin_router
from apps.chore_master_api.web_server.routers.v1.content_delivery import (
    router as content_delivery_router,
)
from apps.chore_master_api.web_server.routers.v1.finance import router as finance_router
from apps.chore_master_api.web_server.routers.v1.identity import (
    router as identity_router,
)
from apps.chore_master_api.web_server.routers.v1.integration import (
    router as integration_router,
)
from apps.chore_master_api.web_server.routers.v1.some_module import (
    router as some_module_router,
)

router = APIRouter(prefix="/v1")

router.include_router(identity_router)
router.include_router(admin_router)
router.include_router(integration_router)
router.include_router(finance_router)
router.include_router(content_delivery_router)
router.include_router(some_module_router)
