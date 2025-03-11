import abc
from typing import Generic, Optional, TypeVar

from apps.chore_master_api.end_user_space.models.base import Entity

ABSTRACT_ENTITY_TYPE = TypeVar("ABSTRACT_ENTITY_TYPE", bound=Entity)
ENTITY_TYPE = TypeVar("ENTITY_TYPE", bound=Entity)

FilterType = Optional[dict]


class BaseRepository(Generic[ABSTRACT_ENTITY_TYPE], metaclass=abc.ABCMeta):
    async def count(self, filter: FilterType = None) -> int:
        count = await self._count(filter=filter)
        return count

    async def insert_many(self, entities: list[ABSTRACT_ENTITY_TYPE]):
        await self._insert_many(entities)

    async def insert_one(self, entity: ABSTRACT_ENTITY_TYPE):
        await self._insert_one(entity)

    async def find_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ) -> list[ABSTRACT_ENTITY_TYPE]:
        entities = await self._find_many(filter=filter, limit=limit)
        return entities

    async def find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        entity = await self._find_one(filter=filter)
        return entity

    async def update_many(
        self, values: dict, filter: FilterType = None
    ) -> list[ABSTRACT_ENTITY_TYPE]:
        return await self._update_many(values=values, filter=filter)

    async def delete_many(self, filter: FilterType = None, limit: Optional[int] = None):
        await self._delete_many(filter=filter, limit=limit)

    @abc.abstractmethod
    async def _count(self, filter: FilterType = None) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def _insert_many(self, entities: list[ABSTRACT_ENTITY_TYPE]):
        raise NotImplementedError

    async def _insert_one(self, entity: ABSTRACT_ENTITY_TYPE):
        await self._insert_many([entity])

    @abc.abstractmethod
    async def _find_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ) -> list[ABSTRACT_ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def _update_many(
        self, values: dict, filter: FilterType = None, limit: Optional[int] = None
    ):
        raise NotImplementedError

    @abc.abstractmethod
    async def _delete_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ):
        raise NotImplementedError
