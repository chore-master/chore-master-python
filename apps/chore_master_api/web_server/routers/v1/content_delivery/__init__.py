from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.content_delivery.post import (
    router as post_router,
)

router = APIRouter(prefix="/content_delivery", tags=["Content Delivery"])

router.include_router(post_router)
