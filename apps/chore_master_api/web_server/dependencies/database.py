from typing import AsyncIterator

from fastapi import Depends, Request

from apps.chore_master_api.config import get_chore_master_api_web_server_config
from apps.chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.base.config import get_base_config
from modules.base.schemas.system import BaseConfigSchema
from modules.database.async_mongo_client import AsyncMongoClient, AsyncMongoDB


async def get_chore_master_api_mongo_client(
    chore_master_api_web_server_config: ChoreMasterAPIWebServerConfigSchema = Depends(
        get_chore_master_api_web_server_config
    ),
) -> AsyncIterator[AsyncMongoClient]:
    async_mongo_client = AsyncMongoClient(
        chore_master_api_web_server_config.MONGODB_URI,
        min_pool_size=1,
        max_pool_size=8,
    )
    yield async_mongo_client
    async_mongo_client.close()


async def get_chore_master_api_db(
    request: Request,
    base_config: BaseConfigSchema = Depends(get_base_config),
) -> AsyncMongoDB:
    chore_master_api_mongo_client: AsyncMongoClient = (
        request.app.state.chore_master_api_mongo_client
    )
    chore_master_api_db = chore_master_api_mongo_client.get_database(
        base_config.SERVICE_NAME
    )
    return chore_master_api_db
