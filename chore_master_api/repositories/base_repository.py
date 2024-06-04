import abc
from typing import Generic, List, Optional, Type, TypeVar

from googleapiclient.discovery import Resource

from chore_master_api.models.base import Entity

ABSTRACT_ENTITY_TYPE = TypeVar("ABSTRACT_ENTITY_TYPE", bound=Entity)
ENTITY_TYPE = TypeVar("ENTITY_TYPE", bound=Entity)

FilterType = Optional[dict]


class AbstractRepository(Generic[ABSTRACT_ENTITY_TYPE], metaclass=abc.ABCMeta):
    async def count(self, filter: FilterType = None) -> int:
        count = await self._count(filter=filter)
        return count

    async def insert_one(self, entity: ABSTRACT_ENTITY_TYPE):
        await self._insert_one(entity)

    async def find_many(self, filter: FilterType = None) -> List[ABSTRACT_ENTITY_TYPE]:
        entities = await self._find_many(filter=filter)
        return entities

    async def find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        entity = await self._find_one(filter=filter)
        return entity

    async def delete_many(self, filter: FilterType = None):
        await self._delete_many(filter=filter)

    @abc.abstractmethod
    async def _count(self, filter: FilterType = None) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def _insert_one(self, entity: ABSTRACT_ENTITY_TYPE):
        raise NotImplementedError

    @abc.abstractmethod
    async def _find_many(self, filter: FilterType = None) -> List[ABSTRACT_ENTITY_TYPE]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        raise NotImplementedError

    @abc.abstractmethod
    async def _delete_many(self, filter: FilterType = None):
        raise NotImplementedError


class SheetRepository(
    Generic[ENTITY_TYPE], AbstractRepository[ENTITY_TYPE], metaclass=abc.ABCMeta
):
    @staticmethod
    def column_name(column_index: int) -> str:
        result = ""
        column_index -= 1
        while column_index > 0:
            column_index, remainder = divmod(column_index - 1, 26)
            result = f"{chr(65 + remainder)}{result}"
        return result

    def __init__(self, sheets_service: Resource, spreadsheet_id: str, sheet_title: str):
        super().__init__()
        self._sheets_service = sheets_service
        self._spreadsheet_id = spreadsheet_id
        self._sheet_title = sheet_title

    @property
    @abc.abstractmethod
    def entity_class(self) -> Type[ENTITY_TYPE]:
        raise NotImplementedError

    async def migrate_schema(self):
        spreadsheet = (
            self._sheets_service.spreadsheets()
            .get(spreadsheetId=self._spreadsheet_id)
            .execute()
        )
        sheets = spreadsheet.get("sheets", [])
        sheet_id = next(
            (
                s["properties"]["sheetId"]
                for s in sheets
                if s["properties"]["title"] == self._sheet_title
            ),
            None,
        )
        column_count = len(self.entity_class.model_fields)
        if sheet_id is None:
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self._spreadsheet_id,
                    body={
                        "requests": [
                            {
                                "addSheet": {
                                    "properties": {
                                        "title": self._sheet_title,
                                        "gridProperties": {
                                            "rowCount": 2,
                                            "columnCount": column_count,
                                        },
                                    }
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
            sheet_id = result["replies"][0]["addSheet"]["properties"]["sheetId"]
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self._spreadsheet_id,
                    body={
                        "requests": [
                            {
                                "updateCells": {
                                    "range": {
                                        "sheetId": sheet_id,
                                        "startRowIndex": 0,
                                        "startColumnIndex": 0,
                                    },
                                    "rows": [
                                        {
                                            "values": [
                                                {
                                                    "userEnteredValue": {
                                                        "stringValue": field_name
                                                    }
                                                }
                                                for field_name in self.entity_class.model_fields.keys()
                                            ]
                                        },
                                        {
                                            "values": [
                                                {
                                                    "userEnteredValue": {
                                                        "stringValue": field_info.annotation.__name__
                                                    }
                                                }
                                                for field_info in self.entity_class.model_fields.values()
                                            ]
                                        },
                                    ],
                                    "fields": "userEnteredValue",
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
        else:
            result = (
                self._sheets_service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._spreadsheet_id,
                    majorDimension="COLUMNS",
                    range=f"{self._sheet_title}!A1:{self.column_name(column_count)}2",
                )
                .execute()
            )
            print(result)

    async def _count(self, filter: FilterType = None) -> int:
        raise NotImplementedError

    async def _insert_one(self, entity: ABSTRACT_ENTITY_TYPE):
        raise NotImplementedError

    async def _find_many(self, filter: FilterType = None) -> List[ABSTRACT_ENTITY_TYPE]:
        raise NotImplementedError

    async def _find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        raise NotImplementedError

    async def _delete_many(self, filter: FilterType = None):
        raise NotImplementedError
