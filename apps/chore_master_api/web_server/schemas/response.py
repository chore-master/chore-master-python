from pydantic import BaseModel


class BaseQueryEntityResponse(BaseModel):
    reference: str
