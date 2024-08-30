from typing import Any, Mapping

from pydantic import BaseModel, Field


class StrategyCommandArgumentSchema(BaseModel):
    args: list[Any] = Field(default_factory=list)
    kwargs: Mapping[str, Any] = Field(default_factory=dict)
