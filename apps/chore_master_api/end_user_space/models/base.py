import shortuuid
from sqlmodel import Field, SQLModel


class Entity(SQLModel):
    reference: str = Field(
        default_factory=lambda: shortuuid.ShortUUID().random(length=8)
    )
