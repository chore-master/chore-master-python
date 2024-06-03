import abc
from typing import Generic, List, Optional, Type, TypeVar

from googleapiclient.discovery import Resource

from chore_master_api.models.base import Entity

ABSTRACT_ENTITY_TYPE = TypeVar("ABSTRACT_ENTITY_TYPE", bound=Entity)
ENTITY_TYPE = TypeVar("ENTITY_TYPE", bound=Entity)


class AbstractRepository(Generic[ABSTRACT_ENTITY_TYPE], metaclass=abc.ABCMeta):
    async def add(self, entity: ABSTRACT_ENTITY_TYPE):
        await self._add(entity)

    async def get_count_by(self, **kwargs) -> int:
        count = await self._get_count_by(**kwargs)
        return count

    async def get_all_by(self, *args, **kwargs) -> List[ABSTRACT_ENTITY_TYPE]:
        entities = await self._get_all_by(*args, **kwargs)
        return entities

    async def get_by(self, *args, **kwargs) -> ABSTRACT_ENTITY_TYPE:
        entity = await self._get_by(*args, **kwargs)
        return entity

    async def delete(self, entity: ABSTRACT_ENTITY_TYPE):
        await self._delete(entity)

    @abc.abstractmethod
    async def _add(self, entity: ABSTRACT_ENTITY_TYPE):
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_count_by(self, **kwargs) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_all_by(self, *args, **kwargs) -> List[ABSTRACT_ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_by(self, *args, **kwargs) -> ABSTRACT_ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def _delete(self, entity: ABSTRACT_ENTITY_TYPE):
        raise NotImplementedError

    @abc.abstractmethod
    async def _delete_by(self, *args, **kwargs):
        raise NotImplementedError


class SheetRepository(
    Generic[ENTITY_TYPE], AbstractRepository[ENTITY_TYPE], metaclass=abc.ABCMeta
):
    def __init__(self, sheets_service: Resource):
        super().__init__()
        self._sheets_service = sheets_service

    @property
    @abc.abstractmethod
    def _entity_class(self) -> Type[ENTITY_TYPE]:
        raise NotImplementedError

    async def _add(self, entity: ENTITY_TYPE):
        raise NotImplementedError

    async def _get_count_by(self, *args, **kwargs) -> int:
        raise NotImplementedError

    async def _get_all_by(self, *args, **kwargs) -> List[ENTITY_TYPE]:
        raise NotImplementedError

    async def _get_by(self, *args, **kwargs) -> Optional[ENTITY_TYPE]:
        raise NotImplementedError

    async def _delete(self, entity: ENTITY_TYPE):
        await self._session.delete(entity)

    async def _delete_by(self, *args, **kwargs):
        entity = await self._get_by(*args, **kwargs)
        await self.delete(entity)

    async def get_by_reference(self, reference: Reference, **kwargs) -> ENTITY_TYPE:
        entity = await self.get_by(reference=reference, **kwargs)
        return entity

    async def delete_by_reference(self, reference: Reference):
        await self._delete_by(reference=reference)
