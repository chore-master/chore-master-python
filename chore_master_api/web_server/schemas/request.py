from pydantic import BaseModel


class EndUserLoginSchema(BaseModel):
    email: str
    password: str
