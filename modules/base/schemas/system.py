from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EnvEnum(Enum):
    LOCAL = "local"
    DEVELOPING = "developing"
    PRODUCTION = "production"


class BaseConfigSchema(BaseModel):
    ENV: EnvEnum
    SERVICE_NAME: str
    COMPONENT_NAME: str
    COMMIT_SHORT_SHA: Optional[str] = None
    COMMIT_REVISION: Optional[str] = None
    IS_IN_DEBUG_MODE: bool
