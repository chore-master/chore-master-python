from sys import gettrace as sys_gettrace

from modules.base.env import get_env
from modules.base.schemas.system import BaseConfigSchema, EnvEnum


def get_base_config() -> BaseConfigSchema:
    ENV = get_env("ENV", default=EnvEnum.PRODUCTION)
    SERVICE_NAME = get_env("SERVICE_NAME")
    COMPONENT_NAME = get_env("COMPONENT_NAME")
    COMMIT_SHORT_SHA = get_env("COMMIT_SHORT_SHA")
    COMMIT_REVISION = get_env("COMMIT_REVISION")
    IS_IN_DEBUG_MODE = sys_gettrace() is not None

    return BaseConfigSchema(
        ENV=ENV,
        SERVICE_NAME=SERVICE_NAME,
        COMPONENT_NAME=COMPONENT_NAME,
        COMMIT_SHORT_SHA=COMMIT_SHORT_SHA,
        COMMIT_REVISION=COMMIT_REVISION,
        IS_IN_DEBUG_MODE=IS_IN_DEBUG_MODE,
    )
