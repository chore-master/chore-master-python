import os
from typing import Any, Optional


def get_env(name: str, default: Optional[str] = None) -> Any:
    return os.environ.get(name, default=default)
