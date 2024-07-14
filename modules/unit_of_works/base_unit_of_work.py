from __future__ import annotations

import abc


class BaseUnitOfWork(abc.ABC):
    async def __aenter__(self) -> BaseUnitOfWork:
        return self

    async def __aexit__(self, *args):
        await self._rollback()

    async def commit(self):
        await self._commit()

    async def rollback(self):
        await self._rollback()

    @abc.abstractmethod
    async def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def _rollback(self):
        raise NotImplementedError
