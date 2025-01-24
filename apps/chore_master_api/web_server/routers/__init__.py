from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1 import router as v1_router
from apps.chore_master_api.web_server.routers.widget import router as widget_router

router = APIRouter()

router.include_router(widget_router)
router.include_router(v1_router)
