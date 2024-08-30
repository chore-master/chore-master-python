from modules.base.config import get_base_config
from modules.base.env import get_env
from modules.base.schemas.system import EnvEnum
from modules.strategy.schemas.config import StrategyManagerConfigSchema


def get_strategy_manager_config() -> StrategyManagerConfigSchema:
    base_config = get_base_config()

    HTTP_SERVER_PORT = int(get_env("HTTP_SERVER_PORT", "11000"))

    if base_config.ENV == EnvEnum.LOCAL:
        pass
    elif base_config.ENV == EnvEnum.DEVELOPING:
        pass
    elif base_config.ENV == EnvEnum.PRODUCTION:
        pass
    return StrategyManagerConfigSchema(
        HTTP_SERVER_PORT=HTTP_SERVER_PORT,
    )
