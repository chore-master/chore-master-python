import os
from typing import Optional

from modules.utils.file_system_utils import FileSystemUtils


class FileSystemCache:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def get(self, keys: list[str]) -> Optional[str]:
        file_path = os.path.join(self._base_dir, *keys)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as f:
            return f.read()

    def set(self, keys: list[str], value: str) -> None:
        file_path = os.path.join(self._base_dir, *keys)
        FileSystemUtils.ensure_directory(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            f.write(value)
