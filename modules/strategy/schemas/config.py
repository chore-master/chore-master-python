from pydantic import BaseModel


class StrategyManagerConfigSchema(BaseModel):
    HTTP_SERVER_PORT: int
