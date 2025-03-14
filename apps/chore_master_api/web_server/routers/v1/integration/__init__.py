from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.integration.feed_operator import (
    router as feed_operator_router,
)
from apps.chore_master_api.web_server.routers.v1.integration.operator import (
    router as operator_router,
)

router = APIRouter(prefix="/integration", tags=["Integration"])
router.include_router(operator_router)
router.include_router(feed_operator_router)
