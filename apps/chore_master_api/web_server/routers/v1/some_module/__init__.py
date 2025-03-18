from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.some_module.some_entity import (
    router as some_entity_router,
)

router = APIRouter()

router.include_router(some_entity_router)
