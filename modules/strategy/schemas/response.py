from typing import Any, Optional

from pydantic import BaseModel


class StrategyCommandResultSchema(BaseModel):
    result: Optional[Any] = None
    error_message: Optional[str] = None
