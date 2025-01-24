from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.finance.market import (
    router as market_router,
)

router = APIRouter(prefix="/finance", tags=["Finance"])

router.include_router(market_router)
