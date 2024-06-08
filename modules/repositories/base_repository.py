import abc
import sys
from typing import Generic, Optional, Type, TypeVar

from chore_master_api.models.base import Entity
from modules.google_service.google_service import GoogleService
from modules.google_service.models.logical_sheet import LogicalSheet

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
    async def _delete_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ):
        raise NotImplementedError


class BaseSheetRepository(
    Generic[ENTITY_TYPE], BaseRepository[ENTITY_TYPE], metaclass=abc.ABCMeta
):
    def __init__(
        self,
        google_service: GoogleService,
        spreadsheet_id: str,
        batch_update_requests: list[dict] = None,
    ):
        super().__init__()
        self._google_service = google_service
        self._spreadsheet_id = spreadsheet_id
        self._batch_update_requests = batch_update_requests

    @property
    @abc.abstractmethod
    def entity_class(self) -> Type[ENTITY_TYPE]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def logical_sheet(self) -> LogicalSheet:
        raise NotImplementedError

    async def _count(self, filter: FilterType = None) -> int:
        raise NotImplementedError

    async def _insert_many(self, entities: list[ABSTRACT_ENTITY_TYPE]):
        reflected_logical_sheet, reflected_sheet_dict, _ = (
            self._google_service.reflect_logical_sheet(
                spreadsheet_id=self._spreadsheet_id,
                sheet_title=self.logical_sheet.logical_name,
                should_include_body=False,
            )
        )
        placeholder_row_values = [
            {} for _ in range(reflected_logical_sheet.preserved_raw_column_count)
        ]
        self._batch_update_requests.append(
            {
                "appendCells": {
                    "sheetId": reflected_sheet_dict["properties"]["sheetId"],
                    "rows": [
                        {
                            "values": placeholder_row_values
                            + [
                                {"userEnteredValue": {"stringValue": cell_value}}
                                for cell_value in row_values
                            ]
                        }
                        for row_values in reflected_logical_sheet.raw_rows_from_entities(
                            entities
                        )
                    ],
                    "fields": "userEnteredValue",
                }
            }
        )

    async def _find_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ) -> list[ABSTRACT_ENTITY_TYPE]:
        if filter is None:
            filter = {}
        if limit is None:
            limit = sys.maxsize
        reflected_logical_sheet, _, reflected_body_values = (
            self._google_service.reflect_logical_sheet(
                spreadsheet_id=self._spreadsheet_id,
                sheet_title=self.logical_sheet.logical_name,
                should_include_body=True,
            )
        )
        entity_class = self.entity_class
        matched_row_dicts, _ = reflected_logical_sheet.match_rows(
            body_values=reflected_body_values, filter=filter, limit=limit
        )
        entities = [entity_class(**row_dict) for row_dict in matched_row_dicts]
        return entities

    async def _find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        entities = await self._find_many(filter=filter, limit=1)
        if len(entities) == 0:
            raise ValueError("Entity not found")
        return entities[0]

    async def _delete_many(
        self, filter: FilterType = None, limit: Optional[int] = None
    ):
        if filter is None:
            filter = {}
        if limit is None:
            limit = sys.maxsize
        reflected_logical_sheet, reflected_sheet_dict, reflected_body_values = (
            self._google_service.reflect_logical_sheet(
                spreadsheet_id=self._spreadsheet_id,
                sheet_title=self.logical_sheet.logical_name,
                should_include_body=True,
            )
        )
        _, matched_row_indices = reflected_logical_sheet.match_rows(
            body_values=reflected_body_values, filter=filter, limit=limit
        )
        for matched_row_index in reversed(matched_row_indices):
            self._batch_update_requests.append(
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": reflected_sheet_dict["properties"]["sheetId"],
                            "dimension": "ROWS",
                            "startIndex": reflected_logical_sheet.preserved_raw_row_count
                            + matched_row_index,
                            "endIndex": reflected_logical_sheet.preserved_raw_row_count
                            + matched_row_index
                            + 1,
                        }
                    }
                }
            )
