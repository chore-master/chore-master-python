from pydantic import BaseModel


class WebServerConfigSchema(BaseModel):
    PORT: int
