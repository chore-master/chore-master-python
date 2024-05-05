from modules.web_server.schemas.config import WebServerConfigSchema


class ChoreMasterAPIWebServerConfigSchema(WebServerConfigSchema):
    UVICORN_AUTO_RELOAD: bool
    ALLOW_ORIGINS: list[str]
    MONGODB_URI: str
