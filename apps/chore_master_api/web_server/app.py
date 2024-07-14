from contextlib import asynccontextmanager
from typing import Optional

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.web_server.dependencies.database import (
    get_chore_master_api_mongo_client,
)
from apps.chore_master_api.web_server.routers.v1.account_center import (
    router as v1_account_center_router,
)
from apps.chore_master_api.web_server.routers.v1.auth import router as v1_auth_router
from apps.chore_master_api.web_server.routers.v1.financial_management import (
    router as v1_financial_management_router,
)
from apps.chore_master_api.web_server.routers.v1.some_module import (
    router as v1_some_module_router,
)
from modules.base.config import get_base_config
from modules.base.schemas.system import BaseConfigSchema
from modules.web_server.base_fastapi import BaseFastAPI


def get_app(base_config: Optional[BaseConfigSchema] = None) -> FastAPI:
    if base_config is None:
        base_config = get_base_config()
    chore_master_api_web_server_config = get_chore_master_api_web_server_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async for chore_master_api_mongo_client in get_chore_master_api_mongo_client(
            chore_master_api_web_server_config
        ):
            app.state.chore_master_api_mongo_client = chore_master_api_mongo_client
            yield

    app = BaseFastAPI(
        base_config=base_config,
        title="Chore Master API",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=chore_master_api_web_server_config.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    base_router = APIRouter()
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(v1_auth_router)
    v1_router.include_router(v1_account_center_router)
    v1_router.include_router(v1_financial_management_router)
    v1_router.include_router(v1_some_module_router)
    base_router.include_router(v1_router)
    app.include_router(base_router)
    return app
