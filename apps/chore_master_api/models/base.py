import shortuuid
from pydantic import BaseModel, Field


class Entity(BaseModel):
    reference: str = Field(
        default_factory=lambda: shortuuid.ShortUUID().random(length=8)
    )
