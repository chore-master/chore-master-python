from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.account_center import (
    router as account_center_router,
)
from apps.chore_master_api.web_server.routers.v1.admin import router as admin_router
from apps.chore_master_api.web_server.routers.v1.finance import router as finance_router
from apps.chore_master_api.web_server.routers.v1.financial_management import (
    router as financial_management_router,
)
from apps.chore_master_api.web_server.routers.v1.infra import router as infra_router
from apps.chore_master_api.web_server.routers.v1.integration import (
    router as integration_router,
)
from apps.chore_master_api.web_server.routers.v1.risk import router as risk_router
from apps.chore_master_api.web_server.routers.v1.some_module import (
    router as some_module_router,
)

router = APIRouter(prefix="/v1")

router.include_router(admin_router)
router.include_router(infra_router)
router.include_router(account_center_router)
router.include_router(integration_router)
router.include_router(financial_management_router)
router.include_router(risk_router)
router.include_router(finance_router)
router.include_router(some_module_router)
