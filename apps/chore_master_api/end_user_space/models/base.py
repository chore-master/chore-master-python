from sqlmodel import Field, SQLModel

from modules.utils.string_utils import StringUtils


class Entity(SQLModel):
    reference: str = Field(default_factory=lambda: StringUtils.new_short_id(length=8))
