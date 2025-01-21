from modules.base.config import get_base_config
from modules.base.env import get_env
from modules.base.schemas.system import EnvEnum
from modules.web_server.schemas.config import WebServerConfigSchema


def get_web_server_config() -> WebServerConfigSchema:
    base_config = get_base_config()

    PORT = int(get_env("PORT", "10000"))

    if base_config.ENV == EnvEnum.LOCAL:
        pass
    elif base_config.ENV == EnvEnum.DEVELOPING:
        pass
    elif base_config.ENV == EnvEnum.PRODUCTION:
        pass

    return WebServerConfigSchema(
        PORT=PORT,
    )
