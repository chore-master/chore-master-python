from pydantic import BaseModel


class EndUserRegisterSchema(BaseModel):
    email: str
    password: str


class EndUserLoginSchema(BaseModel):
    email: str
    password: str
