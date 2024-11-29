import abc
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from apps.chore_master_api.end_user_space.models.base import Entity
from modules.repositories.base_repository import BaseRepository, FilterType

ENTITY_TYPE = TypeVar("ENTITY_TYPE", bound=Entity)


class BaseSQLAlchemyRepository(
    Generic[ENTITY_TYPE], BaseRepository[ENTITY_TYPE], metaclass=abc.ABCMeta
):
    def __init__(self, session: AsyncSession):
        super().__init__()
        self._session = session

    @property
    @abc.abstractmethod
    def entity_class(self) -> Type[ENTITY_TYPE]:
        raise NotImplementedError

    async def _count(self, filter: FilterType = None) -> int:
        if filter is None:
            filter = {}
        statement = select(func.count(self.entity_class.reference)).filter_by(**filter)
        result = await self._session.execute(statement)
        count = result.scalars().unique().first()
        return count

    async def _insert_many(self, entities: list[ENTITY_TYPE]):
        for entity in entities:
            self._session.add(entity)

    async def _find_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ) -> list[ENTITY_TYPE]:
        if filter is None:
            filter = {}
        statement = select(self.entity_class).filter_by(**filter).limit(limit)
        result = await self._session.execute(statement)
        entities = result.scalars().unique().all()
        return entities

    async def _find_one(self, filter: FilterType = None) -> ENTITY_TYPE:
        if filter is None:
            filter = {}
        statement = select(self.entity_class).filter_by(**filter)
        result = await self._session.execute(statement)
        entity = result.scalars().unique().one()
        return entity

    async def _update_many(self, values: dict, filter: FilterType = None):
        if filter is None:
            filter = {}
        statement = update(self.entity_class).filter_by(**filter).values(values)
        _result = await self._session.execute(statement)

    async def _delete_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ):
        entities = await self._find_many(filter=filter, limit=limit)
        for entity in entities:
            await self._session.delete(entity)
