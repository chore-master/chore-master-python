from chore_master_api.web_server.schemas.config import (
    ChoreMasterAPIWebServerConfigSchema,
)
from modules.base.config import get_base_config
from modules.base.env import get_env
from modules.base.schemas.system import EnvEnum
from modules.web_server.config import get_web_server_config


def get_chore_master_api_web_server_config() -> ChoreMasterAPIWebServerConfigSchema:
    base_config = get_base_config()
    web_server_config = get_web_server_config()

    UVICORN_AUTO_RELOAD = False
    ALLOW_ORIGINS = ["*"]
    MONGODB_URI = get_env("MONGODB_URI")

    if base_config.ENV == EnvEnum.LOCAL:
        UVICORN_AUTO_RELOAD = True
    elif base_config.ENV == EnvEnum.DEVELOPING:
        pass
    elif base_config.ENV == EnvEnum.PRODUCTION:
        pass

    return ChoreMasterAPIWebServerConfigSchema(
        **web_server_config.model_dump(),
        UVICORN_AUTO_RELOAD=UVICORN_AUTO_RELOAD,
        ALLOW_ORIGINS=ALLOW_ORIGINS,
        MONGODB_URI=MONGODB_URI,
    )
