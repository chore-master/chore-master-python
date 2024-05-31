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
    MONGODB_URI = get_env("MONGODB_URI")

    FRONTEND_ORIGIN = None
    IAM_API_ORIGIN = None
    ALLOW_ORIGINS = ["*"]

    SESSION_COOKIE_KEY = "end_user_session_reference"
    SESSION_COOKIE_DOMAIN = "localhost"
    GOOGLE_OAUTH_CLIENT_ID = get_env("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_SECRET = get_env("GOOGLE_OAUTH_SECRET")

    if base_config.ENV == EnvEnum.LOCAL:
        UVICORN_AUTO_RELOAD = True
        FRONTEND_ORIGIN = "http://localhost:3000"
        ALLOW_ORIGINS = [FRONTEND_ORIGIN]
        IAM_API_ORIGIN = "http://localhost:13000"
        SESSION_COOKIE_DOMAIN = "localhost"
    elif base_config.ENV == EnvEnum.DEVELOPING:
        FRONTEND_ORIGIN = "https://dev--chore-master.lation.app"
        ALLOW_ORIGINS = [FRONTEND_ORIGIN]
        IAM_API_ORIGIN = "https://dev--chore-master-api.lation.app"
        SESSION_COOKIE_DOMAIN = "dev--chore-master-api.lation.app"
    elif base_config.ENV == EnvEnum.PRODUCTION:
        FRONTEND_ORIGIN = "https://chore-master.lation.app"
        ALLOW_ORIGINS = [FRONTEND_ORIGIN]
        IAM_API_ORIGIN = "https://chore-master-api.lation.app"
        SESSION_COOKIE_DOMAIN = "chore-master-api.lation.app"

    return ChoreMasterAPIWebServerConfigSchema(
        **web_server_config.model_dump(),
        UVICORN_AUTO_RELOAD=UVICORN_AUTO_RELOAD,
        ALLOW_ORIGINS=ALLOW_ORIGINS,
        MONGODB_URI=MONGODB_URI,
        FRONTEND_ORIGIN=FRONTEND_ORIGIN,
        IAM_API_ORIGIN=IAM_API_ORIGIN,
        SESSION_COOKIE_KEY=SESSION_COOKIE_KEY,
        SESSION_COOKIE_DOMAIN=SESSION_COOKIE_DOMAIN,
        GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_ID,
        GOOGLE_OAUTH_SECRET=GOOGLE_OAUTH_SECRET,
    )
