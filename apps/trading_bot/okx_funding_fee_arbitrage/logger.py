import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Callable, Optional


# https://alexandra-zaharia.github.io/posts/custom-logger-in-python-for-stdout-and-or-file-log/
class Logger(logging.getLoggerClass()):
    def __init__(self, name: str):
        super().__init__(name)
        self._name = name
        self.setLevel(logging.DEBUG)
        self._stdout_handler = None
        self._file_hanlder = None
        self._time_rotating_file_handler = None

    def enable_stdout_handler(self):
        if self._stdout_handler is not None:
            return
        self._stdout_handler = logging.StreamHandler(sys.stdout)
        self._stdout_handler.setLevel(logging.DEBUG)
        self._stdout_handler.setFormatter(self._get_formatter())
        self.addHandler(self._stdout_handler)

    def enable_file_handler(self, root_dir: Optional[str] = None):
        if self._file_hanlder is not None:
            return
        if root_dir is None:
            root_dir = "./"
        target_dirname = os.path.dirname(os.path.join(root_dir, self._name))
        now = datetime.utcnow().strftime("%Y_%m_%d_%H_%M_%S_%f")
        target_basename = f"{os.path.basename(self._name)}_{now}.log"
        if not os.path.isdir(target_dirname):
            os.makedirs(target_dirname)
        self._file_hanlder = logging.FileHandler(
            os.path.join(target_dirname, target_basename)
        )
        self._file_hanlder.setLevel(logging.DEBUG)
        self._file_hanlder.setFormatter(self._get_formatter())
        self.addHandler(self._file_hanlder)

    def enable_time_rotating_file_handler(
        self, when: str = "midnight", interval: int = 1
    ):
        if self._time_rotating_file_handler is not None:
            return
        self._time_rotating_file_handler = TimedRotatingFileHandler(
            f"{self._name}", when=when, interval=interval
        )
        self._time_rotating_file_handler.suffix = "%Y_%m_%d_%H_%M_%S.log"
        self._time_rotating_file_handler.setLevel(logging.DEBUG)
        self._time_rotating_file_handler.setFormatter(self._get_formatter())
        self.addHandler(self._time_rotating_file_handler)

    def _get_formatter(self) -> logging.Formatter:
        return logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    def _custom_log(
        self,
        func: Callable,
        msg,
        *args,
        flush: bool = False,
        metadata: Optional[dict] = None,
        **kwargs,
    ):
        merged_msg = msg
        if metadata is not None:
            merged_msg = f"{merged_msg}\n{json.dumps(metadata, indent=4)}"
        func(merged_msg, *args, **kwargs)
        if flush:
            if self._file_hanlder:
                self._file_hanlder.flush()
            if self._time_rotating_file_handler:
                self._time_rotating_file_handler.flush()

    def debug(self, *args, **kwargs):
        self._custom_log(super().debug, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._custom_log(super().info, msg, *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._custom_log(super().warning, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._custom_log(super().error, msg, *args, **kwargs)

    def critical(self, *args, **kwargs):
        self._custom_log(super().critical, *args, **kwargs)
