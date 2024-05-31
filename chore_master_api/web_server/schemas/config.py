from modules.web_server.schemas.config import WebServerConfigSchema


class ChoreMasterAPIWebServerConfigSchema(WebServerConfigSchema):
    UVICORN_AUTO_RELOAD: bool
    MONGODB_URI: str

    IAM_API_ORIGIN: str
    FRONTEND_ORIGIN: str
    ALLOW_ORIGINS: list[str]

    SESSION_COOKIE_KEY: str
    SESSION_COOKIE_DOMAIN: str

    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_SECRET: str
