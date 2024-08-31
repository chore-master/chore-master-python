import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import timedelta

import shortuuid
from dotenv import dotenv_values


class StrategyUtils:
    @staticmethod
    def new_short_id() -> str:
        return shortuuid.ShortUUID().random(length=5)

    @staticmethod
    @asynccontextmanager
    async def okx_context_manager(config_path: str, sandbox_mode: bool = False):
        import ccxt.pro

        config = dotenv_values(config_path)
        exchange = ccxt.pro.okx(
            {
                "apiKey": config["OKX_API_KEY"],
                "secret": config["OKX_SECRET_KEY"],
                "password": config["OKX_PASSPHRASE"],
                "enableRateLimit": True,
            }
        )
        exchange.set_sandbox_mode(sandbox_mode)
        yield exchange
        await exchange.close()

    @staticmethod
    def ensure_directory(directory_path: str):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

    @staticmethod
    async def tick_every(interval: timedelta):
        interval_sec = interval.total_seconds()
        while True:
            iteration_start_time_sec = time.monotonic()
            yield
            elapsed_time_sec = time.monotonic() - iteration_start_time_sec
            await asyncio.sleep(max(0, interval_sec - elapsed_time_sec))
