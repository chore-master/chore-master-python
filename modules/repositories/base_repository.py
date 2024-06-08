import abc
from typing import Generic, List, Optional, Type, TypeVar

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
    async def _insert_many(self, entities: list[ABSTRACT_ENTITY_TYPE]):
        raise NotImplementedError

    async def _insert_one(self, entity: ABSTRACT_ENTITY_TYPE):
        await self._insert_many([entity])

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
    # attribute_type_to_sheet_type_name_map = {
    #     bool: TypeNameEnum.BOOLEAN.value,
    #     int: TypeNameEnum.INTEGER.value,
    #     float: TypeNameEnum.FLOAT.value,
    #     str: TypeNameEnum.STRING.value,
    #     Decimal: TypeNameEnum.DECIMAL.value,
    #     UUID: TypeNameEnum.UUID.value,
    # }
    # sheet_type_name_to_attribute_type_map = {
    #     v: k for k, v in attribute_type_to_sheet_type_name_map.items()
    # }

    def __init__(self, google_service: GoogleService, spreadsheet_id: str):
        super().__init__()
        self._google_service = google_service
        self._spreadsheet_id = spreadsheet_id

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
        grid_dict = reflected_sheet_dict["properties"]["gridProperties"]
        reflected_column_count = grid_dict["columnCount"]
        reflected_row_count = grid_dict["rowCount"]
        left_column_name = self._google_service.sheet_column_name(
            reflected_logical_sheet.preserved_raw_column_count
        )
        right_column_name = self._google_service.sheet_column_name(
            reflected_column_count - 1
        )
        body_range = f"{self.logical_sheet.logical_name}!{left_column_name}{reflected_logical_sheet.preserved_raw_row_count + 1}:{right_column_name}{reflected_row_count}"
        result = (
            self._google_service._sheets_service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self._spreadsheet_id,
                range=body_range,
                valueInputOption="RAW",
                body={
                    "values": reflected_logical_sheet.raw_rows_from_entities(entities)
                },
            )
            .execute()
        )

    async def _find_many(self, filter: FilterType = None) -> List[ABSTRACT_ENTITY_TYPE]:
        raise NotImplementedError

    async def _find_one(self, filter: FilterType = None) -> ABSTRACT_ENTITY_TYPE:
        raise NotImplementedError

    async def _delete_many(self, filter: FilterType = None):
        raise NotImplementedError
