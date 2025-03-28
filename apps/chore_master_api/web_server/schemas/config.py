from typing import Optional

from modules.web_server.schemas.config import WebServerConfigSchema


class ChoreMasterAPIWebServerConfigSchema(WebServerConfigSchema):
    UVICORN_AUTO_RELOAD: bool
    DATABASE_ORIGIN: str
    DATABASE_SCHEMA_NAME: Optional[str] = None

    FRONTEND_ORIGIN: str
    ALLOW_ORIGINS: list[str]

    SESSION_COOKIE_KEY: str
    SESSION_COOKIE_DOMAIN: str

    CLOUDFLARE_TURNSTILE_SECRET_KEY: Optional[str] = None
    CLOUDFLARE_TURNSTILE_VERIFY_URL: str
