from typing import Optional

import shortuuid
from pydantic import BaseModel, Field


class BaseCreateEntityRequest(BaseModel):
    reference: Optional[str] = Field(
        default_factory=lambda: shortuuid.ShortUUID().random(length=8)
    )


class BaseUpdateEntityRequest(BaseModel):
    pass


class EndUserRegisterSchema(BaseModel):
    email: str
    password: str


class EndUserLoginSchema(BaseModel):
    email: str
    password: str
