from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.integration.resource import (
    router as resource_router,
)

router = APIRouter(prefix="/integration", tags=["Integration"])
router.include_router(resource_router)
