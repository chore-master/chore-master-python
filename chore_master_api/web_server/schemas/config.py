from modules.web_server.schemas.config import WebServerConfigSchema


class ChoreMasterAPIWebServerConfigSchema(WebServerConfigSchema):
    UVICORN_AUTO_RELOAD: bool
    ALLOW_ORIGINS: list[str]
    MONGODB_URI: str

    HOST: str
    SESSION_COOKIE_KEY: str
    SESSION_COOKIE_DOMAIN: str

    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_SECRET: str
