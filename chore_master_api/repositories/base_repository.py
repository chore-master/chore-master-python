import abc
from typing import Generic, List, Optional, Type, TypeVar

from googleapiclient.discovery import Resource

from chore_master_api.models.base import Entity

ABSTRACT_ENTITY_TYPE = TypeVar("ABSTRACT_ENTITY_TYPE", bound=Entity)
ENTITY_TYPE = TypeVar("ENTITY_TYPE", bound=Entity)

FilterType = Optional[dict]


class BaseRepository(Generic[ABSTRACT_ENTITY_TYPE], metaclass=abc.ABCMeta):
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


class BaseSheetRepository(
    Generic[ENTITY_TYPE], BaseRepository[ENTITY_TYPE], metaclass=abc.ABCMeta
):
    @staticmethod
    def column_name(column_index: int) -> str:
        result = ""
        column_index -= 1
        while column_index > 0:
            column_index, remainder = divmod(column_index - 1, 26)
            result = f"{chr(65 + remainder)}{result}"
        return result

    def __init__(self, sheets_service: Resource, spreadsheet_id: str):
        super().__init__()
        self._sheets_service = sheets_service
        self._spreadsheet_id = spreadsheet_id

    @property
    @abc.abstractmethod
    def entity_class(self) -> Type[ENTITY_TYPE]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    async def sheet_title(self) -> str:
        raise NotImplementedError

    async def migrate_schema(self):
        spreadsheet = (
            self._sheets_service.spreadsheets()
            .get(spreadsheetId=self._spreadsheet_id)
            .execute()
        )
        sheets = spreadsheet.get("sheets", [])
        sheet = next(
            (s for s in sheets if s["properties"]["title"] == self.sheet_title),
            None,
        )
        if sheet is None:
            # create table
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self._spreadsheet_id,
                    body={
                        "requests": [
                            {
                                "addSheet": {
                                    "properties": {
                                        "title": self.sheet_title,
                                        "gridProperties": {
                                            "rowCount": 2,
                                            "columnCount": 1,  # 0 will result in columns A-Z
                                        },
                                    }
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
            sheet = result["replies"][0]["addSheet"]

        # update table

        sheet_id = sheet["properties"]["sheetId"]
        reflected_column_count = sheet["properties"]["gridProperties"]["columnCount"]
        batch_udpate_requests = []
        delete_column_count = 0

        # reflect table
        result = (
            self._sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=self._spreadsheet_id,
                majorDimension="COLUMNS",
                range=f"{self.sheet_title}!A1:{self.column_name(reflected_column_count)}2",
            )
            .execute()
        )
        field_names_set = set(self.entity_class.model_fields.keys())
        reflected_field_names_set = set()
        reflected_values = result.get("values", [])
        for column_index in range(reflected_column_count):
            # delete redundant columns
            if column_index >= len(reflected_values):
                batch_udpate_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index - delete_column_count,
                                "endIndex": column_index - delete_column_count + 1,
                            }
                        }
                    }
                )
                delete_column_count += 1
                continue

            # delete redundant columns
            series = reflected_values[column_index]
            if len(series) != 2:
                batch_udpate_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index - delete_column_count,
                                "endIndex": column_index - delete_column_count + 1,
                            }
                        }
                    }
                )
                delete_column_count += 1
                continue

            # delete deprecated columns
            reflected_field_name, reflected_field_type_name = series
            reflected_field_names_set.add(reflected_field_name)
            if reflected_field_name not in self.entity_class.model_fields:
                batch_udpate_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index - delete_column_count,
                                "endIndex": column_index - delete_column_count + 1,
                            }
                        }
                    }
                )
                delete_column_count += 1
                continue

            # update columns
            field_info = self.entity_class.model_fields[reflected_field_name]
            field_type_name = field_info.annotation.__name__
            if reflected_field_type_name != field_type_name:
                batch_udpate_requests.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 1,
                                "startColumnIndex": column_index,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": field_type_name
                                            }
                                        }
                                    ]
                                },
                            ],
                            "fields": "userEnteredValue",
                        }
                    }
                )

        # create columns
        new_field_names_set = field_names_set.difference(reflected_field_names_set)
        insert_column_start_index = reflected_column_count - delete_column_count
        new_columns_count = len(new_field_names_set)
        if new_columns_count > 0:
            batch_udpate_requests.append(
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": insert_column_start_index,
                            "endIndex": insert_column_start_index + new_columns_count,
                        },
                        "inheritFromBefore": insert_column_start_index > 0,
                    }
                }
            )

            for i, field_name in enumerate(new_field_names_set):
                field_info = self.entity_class.model_fields[field_name]
                batch_udpate_requests.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "startColumnIndex": insert_column_start_index + i,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": field_name
                                            }
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": field_info.annotation.__name__
                                            }
                                        }
                                    ]
                                },
                            ],
                            "fields": "userEnteredValue",
                        }
                    }
                )

        if len(batch_udpate_requests) > 0:
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self._spreadsheet_id,
                    body={"requests": batch_udpate_requests},
                )
                .execute()
            )
            print("Migration done", batch_udpate_requests, result)
        else:
            print("Migration done: no difference")

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
