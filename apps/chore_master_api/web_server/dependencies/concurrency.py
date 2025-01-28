import asyncio
from typing import AsyncIterator

from fastapi import Request

from modules.web_server.exceptions import BadRequestError


async def get_mutex(request: Request) -> AsyncIterator[asyncio.Lock]:
    mutex: asyncio.Lock = request.app.state.mutex
    if mutex.locked():
        raise BadRequestError("Mutex is locked")
    async with mutex:
        yield mutex
