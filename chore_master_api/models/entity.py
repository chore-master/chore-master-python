from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Entity(BaseModel):
    reference: UUID = Field(default_factory=uuid4)
