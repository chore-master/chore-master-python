from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer
from sqlmodel import Field, SQLModel

from modules.utils.string_utils import StringUtils

SerializableDecimal = Annotated[
    Decimal,
    PlainSerializer(
        lambda d: "{:f}".format(d.normalize()), return_type=str, when_used="json"
    ),
]


class Entity(SQLModel):
    reference: str = Field(default_factory=lambda: StringUtils.new_short_id(length=8))
