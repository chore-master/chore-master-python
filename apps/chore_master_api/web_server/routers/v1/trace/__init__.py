from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.trace.quota import (
    router as quota_router,
)

router = APIRouter(prefix="/trace", tags=["Trace"])
router.include_router(quota_router)
