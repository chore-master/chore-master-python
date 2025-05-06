from fastapi import APIRouter

from apps.chore_master_api.web_server.routers.v1.finance.account import (
    router as account_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.asset import (
    router as asset_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.balance_sheet import (
    router as balance_sheet_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.market import (
    router as market_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.portfolio import (
    router as portfolio_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.price import (
    router as price_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.transaction import (
    router as transaction_router,
)
from apps.chore_master_api.web_server.routers.v1.finance.transfer import (
    router as transfer_router,
)

router = APIRouter(prefix="/finance", tags=["Finance"])

router.include_router(market_router)
router.include_router(account_router)
router.include_router(asset_router)
router.include_router(price_router)
router.include_router(balance_sheet_router)
router.include_router(portfolio_router)
router.include_router(transaction_router)
router.include_router(transfer_router)
