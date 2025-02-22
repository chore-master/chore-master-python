from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer


class BaseQueryEntityResponse(BaseModel):
    reference: str


SerializableDecimal = Annotated[
    Decimal,
    PlainSerializer(
        lambda d: "{:f}".format(d.normalize()), return_type=str, when_used="json"
    ),
]
