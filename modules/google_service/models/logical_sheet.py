from collections import namedtuple
from enum import Enum
from typing import NamedTuple, Optional

from pydantic import BaseModel, ConfigDict


class LogicalDataTypeNameEnum(str, Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    DATETIME = "DATETIME"
    DECIMAL = "DECIMAL"
    UUID = "UUID"


class LogicalColumn(BaseModel):
    model_config = ConfigDict(use_enum_values=True, frozen=True)

    logical_name: str
    logical_data_type_name: Optional[LogicalDataTypeNameEnum]
    logical_is_nullable: Optional[bool] = False
    logical_is_primary_key: Optional[bool] = False
    logical_is_unique_key: Optional[bool] = False

    raw_index: Optional[int] = None


class LogicalSheet(BaseModel):
    model_config = ConfigDict(frozen=True)

    logical_name: str
    logical_columns: list[LogicalColumn]

    preserved_raw_row_names: NamedTuple = namedtuple(
        "PreservedRawRowNames",
        [
            "logical_column_name",
            "logical_data_type",
            "logical_is_nullable",
            "logical_is_primary_key",
            "logical_is_unique_key",
        ],
    )
    preserved_raw_column_names: NamedTuple = namedtuple(
        "PreservedRawColumnNames",
        [
            "placeholder_column",  # spreadsheet doesn't allow column count become zero
        ],
    )

    @property
    def preserved_raw_row_count(self) -> int:
        return len(self.preserved_raw_row_names._fields)

    @property
    def preserved_raw_column_count(self) -> int:
        return len(self.preserved_raw_column_names._fields)
