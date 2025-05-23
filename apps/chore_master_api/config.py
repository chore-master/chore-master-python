from apps.chore_master_api.web_server.schemas.config import (
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
    DATABASE_ORIGIN = get_env("DATABASE_ORIGIN")
    DATABASE_SCHEMA_NAME = get_env("DATABASE_SCHEMA_NAME")
    API_ORIGIN = get_env("API_ORIGIN")
    FRONTEND_ORIGIN = get_env("FRONTEND_ORIGIN")
    ALLOW_ORIGINS = ["*"]

    SESSION_COOKIE_KEY = "cm_end_user_session_reference"
    SESSION_COOKIE_DOMAIN = "localhost"

    CLOUDFLARE_TURNSTILE_SECRET_KEY = get_env("CLOUDFLARE_TURNSTILE_SECRET_KEY")
    CLOUDFLARE_TURNSTILE_VERIFY_URL = (
        "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    )

    GOOGLE_OAUTH_ENDPOINT = get_env(
        "GOOGLE_OAUTH_ENDPOINT", "https://accounts.google.com/o/oauth2/v2/auth"
    )
    GOOGLE_OAUTH_TOKEN_URI = get_env(
        "GOOGLE_OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token"
    )
    GOOGLE_OAUTH_JWKS_URI = get_env(
        "GOOGLE_OAUTH_JWKS_URI", "https://www.googleapis.com/oauth2/v3/certs"
    )
    GOOGLE_OAUTH_CLIENT_ID = get_env("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_SECRET = get_env("GOOGLE_OAUTH_SECRET")

    if base_config.ENV == EnvEnum.LOCAL:
        UVICORN_AUTO_RELOAD = True
        API_ORIGIN = get_env("API_ORIGIN", "http://localhost:10000")
        FRONTEND_ORIGIN = get_env("FRONTEND_ORIGIN", "http://localhost:2000")
        ALLOW_ORIGINS = [FRONTEND_ORIGIN]
        SESSION_COOKIE_DOMAIN = "localhost"
    elif base_config.ENV == EnvEnum.DEVELOPING:
        API_ORIGIN = get_env("API_ORIGIN", "https://dev-api.chore-master.app")
        FRONTEND_ORIGIN = get_env("FRONTEND_ORIGIN", "https://dev.chore-master.app")
        ALLOW_ORIGINS = [FRONTEND_ORIGIN]
        SESSION_COOKIE_DOMAIN = "dev-api.chore-master.app"
    elif base_config.ENV == EnvEnum.PRODUCTION:
        API_ORIGIN = get_env("API_ORIGIN", "https://api.chore-master.app")
        FRONTEND_ORIGIN = get_env("FRONTEND_ORIGIN", "https://www.chore-master.app")
        ALLOW_ORIGINS = [FRONTEND_ORIGIN]
        SESSION_COOKIE_DOMAIN = "api.chore-master.app"

    return ChoreMasterAPIWebServerConfigSchema(
        **web_server_config.model_dump(),
        UVICORN_AUTO_RELOAD=UVICORN_AUTO_RELOAD,
        ALLOW_ORIGINS=ALLOW_ORIGINS,
        DATABASE_ORIGIN=DATABASE_ORIGIN,
        DATABASE_SCHEMA_NAME=DATABASE_SCHEMA_NAME,
        API_ORIGIN=API_ORIGIN,
        FRONTEND_ORIGIN=FRONTEND_ORIGIN,
        SESSION_COOKIE_KEY=SESSION_COOKIE_KEY,
        SESSION_COOKIE_DOMAIN=SESSION_COOKIE_DOMAIN,
        CLOUDFLARE_TURNSTILE_SECRET_KEY=CLOUDFLARE_TURNSTILE_SECRET_KEY,
        CLOUDFLARE_TURNSTILE_VERIFY_URL=CLOUDFLARE_TURNSTILE_VERIFY_URL,
        GOOGLE_OAUTH_ENDPOINT=GOOGLE_OAUTH_ENDPOINT,
        GOOGLE_OAUTH_TOKEN_URI=GOOGLE_OAUTH_TOKEN_URI,
        GOOGLE_OAUTH_JWKS_URI=GOOGLE_OAUTH_JWKS_URI,
        GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_ID,
        GOOGLE_OAUTH_SECRET=GOOGLE_OAUTH_SECRET,
    )
