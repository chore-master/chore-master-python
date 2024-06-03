import abc
from typing import Generic, List, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import expression

from modules.domain.models.entity import Entity
from modules.domain.types import Reference
from modules.domain.views.view_enhancer import ViewEnhancement

ABSTRACT_MODEL = TypeVar("ABSTRACT_MODEL", bound=Entity)
MODEL = TypeVar("MODEL", bound=Entity)


class AbstractRepository(Generic[ABSTRACT_MODEL], metaclass=abc.ABCMeta):
    async def add(self, entity: ABSTRACT_MODEL):
        await self._add(entity)

    async def get_count_by(self, **kwargs) -> int:
        count = await self._get_count_by(**kwargs)
        return count

    async def get_all_by(self, *args, **kwargs) -> List[ABSTRACT_MODEL]:
        entities = await self._get_all_by(*args, **kwargs)
        return entities

    async def get_by(self, *args, **kwargs) -> ABSTRACT_MODEL:
        entity = await self._get_by(*args, **kwargs)
        return entity

    async def delete(self, entity: ABSTRACT_MODEL):
        await self._delete(entity)

    @abc.abstractmethod
    async def _add(self, entity: ABSTRACT_MODEL):
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_count_by(self, **kwargs) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_all_by(self, *args, **kwargs) -> List[ABSTRACT_MODEL]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_by(self, *args, **kwargs) -> ABSTRACT_MODEL:
        raise NotImplementedError

    @abc.abstractmethod
    async def _delete(self, entity: ABSTRACT_MODEL):
        raise NotImplementedError

    @abc.abstractmethod
    async def _delete_by(self, *args, **kwargs):
        raise NotImplementedError


class SqlAlchemyRepository(
    Generic[MODEL], AbstractRepository[MODEL], metaclass=abc.ABCMeta
):
    def __init__(self, session: AsyncSession):
        super().__init__()
        self._session = session

    @property
    @abc.abstractmethod
    def _model(self) -> Type[MODEL]:
        raise NotImplemented

    def get_enhanced_select_statement(
        self, statement: expression.select
    ) -> expression.select:
        return statement

    async def _add(self, entity: MODEL):
        self._session.add(entity)

    async def _get_count_by(
        self, *args, view_enhancements: List[ViewEnhancement] = None, **kwargs
    ) -> int:
        statement = (
            select(func.count(self._model.reference)).filter(*args).filter_by(**kwargs)
        )
        if view_enhancements is not None:
            for view_enhancement in view_enhancements:
                statement = view_enhancement.enhancer.enhance(
                    statement, view_enhancement.context
                )
        result = await self._session.execute(statement)
        count = result.scalars().unique().first()
        return count

    async def _get_all_by(
        self, *args, view_enhancements: List[ViewEnhancement] = None, **kwargs
    ) -> List[MODEL]:
        statement = self.get_enhanced_select_statement(
            select(self._model).filter(*args).filter_by(**kwargs)
        )
        if view_enhancements is not None:
            for view_enhancement in view_enhancements:
                statement = view_enhancement.enhancer.enhance(
                    statement, view_enhancement.context
                )
        result = await self._session.execute(statement)
        entities = result.scalars().unique().all()
        return entities

    async def _get_by(
        self, *args, view_enhancements: List[ViewEnhancement] = None, **kwargs
    ) -> MODEL | None:
        statement = self.get_enhanced_select_statement(
            select(self._model).filter(*args).filter_by(**kwargs)
        )
        if view_enhancements is not None:
            for view_enhancement in view_enhancements:
                statement = view_enhancement.enhancer.enhance(
                    statement, view_enhancement.context
                )
        result = await self._session.execute(statement)
        entity = result.scalars().unique().first()
        return entity

    async def _delete(self, entity: MODEL):
        await self._session.delete(entity)

    async def _delete_by(self, *args, **kwargs):
        entity = await self._get_by(*args, **kwargs)
        await self.delete(entity)

    async def get_by_reference(self, reference: Reference, **kwargs) -> MODEL:
        entity = await self.get_by(reference=reference, **kwargs)
        return entity

    async def delete_by_reference(self, reference: Reference):
        await self._delete_by(reference=reference)

    # deprecating, use _get_count_by(view_enhancements=...) instead
    async def get_count_by_view_enhancements(
        self, view_enhancements: List[ViewEnhancement]
    ) -> int:
        statement = select(func.count(self._model.reference))
        for view_enhancement in view_enhancements:
            statement = view_enhancement.enhancer.enhance(
                statement, view_enhancement.context
            )
        result = await self._session.execute(statement)
        count = result.scalars().unique().first()
        return count

    # deprecating, use _get_all_by(view_enhancements=...) instead
    async def get_all_by_view_enhancements(
        self, view_enhancements: List[ViewEnhancement]
    ) -> List[MODEL]:
        statement = select(self._model)
        for view_enhancement in view_enhancements:
            statement = view_enhancement.enhancer.enhance(
                statement, view_enhancement.context
            )
        result = await self._session.execute(statement)
        entities = result.scalars().unique().all()
        return entities

    # deprecating, use _get_by(view_enhancements=...) instead
    async def get_by_view_enhancements(
        self, view_enhancements: List[ViewEnhancement]
    ) -> MODEL:
        statement = select(self._model)
        for view_enhancement in view_enhancements:
            statement = view_enhancement.enhancer.enhance(
                statement, view_enhancement.context
            )
        result = await self._session.execute(statement)
        entity = result.scalars().first()
        return entity
