from typing import Optional

from modules.web_server.schemas.config import WebServerConfigSchema


class ChoreMasterAPIWebServerConfigSchema(WebServerConfigSchema):
    UVICORN_AUTO_RELOAD: bool
    DATABASE_ORIGIN: str
    DATABASE_SCHEMA_NAME: Optional[str] = None

    API_ORIGIN: str
    FRONTEND_ORIGIN: str
    ALLOW_ORIGINS: list[str]

    SESSION_COOKIE_KEY: str
    SESSION_COOKIE_DOMAIN: str

    CLOUDFLARE_TURNSTILE_SECRET_KEY: Optional[str] = None
    CLOUDFLARE_TURNSTILE_VERIFY_URL: str

    GOOGLE_OAUTH_ENDPOINT: Optional[str] = None
    GOOGLE_OAUTH_TOKEN_URI: Optional[str] = None
    GOOGLE_OAUTH_JWKS_URI: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_SECRET: Optional[str] = None
