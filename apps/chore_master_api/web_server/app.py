import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.end_user_space.mapper import Mapper

# from apps.chore_master_api.service_layers.onboarding import ensure_system_initialized
# from apps.chore_master_api.web_server.dependencies.database import get_schema_migration
from apps.chore_master_api.web_server.routers import router as base_router
from modules.base.config import get_base_config
from modules.base.schemas.system import BaseConfigSchema
from modules.database.relational_database import RelationalDatabase
from modules.web_server.base_fastapi import BaseFastAPI


def get_app(base_config: Optional[BaseConfigSchema] = None) -> FastAPI:
    if base_config is None:
        base_config = get_base_config()
    chore_master_api_web_server_config = get_chore_master_api_web_server_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        chore_master_db = RelationalDatabase(
            chore_master_api_web_server_config.DATABASE_ORIGIN
        )

        metadata = RelationalDatabase.create_metadata(
            schema_name=chore_master_api_web_server_config.DATABASE_SCHEMA_NAME
        )
        chore_master_db_registry = RelationalDatabase.create_mapper_registry(
            metadata=metadata
        )
        Mapper(chore_master_db_registry).map_models_to_tables()

        # schema_migration = await get_schema_migration(chore_master_db)
        # await ensure_system_initialized(
        #     chore_master_db=chore_master_db,
        #     chore_master_db_registry=chore_master_db_registry,
        #     schema_migration=schema_migration,
        # )
        app.state.chore_master_db = chore_master_db
        app.state.chore_master_db_registry = chore_master_db_registry
        app.state.mutex = asyncio.Lock()
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
    app.include_router(base_router)
    return app
