from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.admin.database import (
    router as database_router,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(database_router)
