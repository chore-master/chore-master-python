from collections import namedtuple
from enum import Enum
from typing import NamedTuple, Optional

from pydantic import BaseModel, ConfigDict

from chore_master_api.models.base import Entity


class LogicalDataTypeNameEnum(str, Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    DATETIME = "DATETIME"
    DECIMAL = "DECIMAL"
    UUID = "UUID"


class LogicalColumn(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True, frozen=True, arbitrary_types_allowed=False
    )

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

    def raw_rows_from_entities(self, entities: list[Entity]) -> list:
        rows = []
        for entity in entities:
            entity_values = [None for _ in range(len(self.logical_columns))]
            for logical_column in self.logical_columns:
                py_value = getattr(entity, logical_column.logical_name)
                if py_value is None:
                    if not logical_column.logical_is_nullable:
                        raise ValueError(
                            f"Non-nullable column {logical_column.logical_name} is None"
                        )
                    py_value = ""
                match logical_column.logical_data_type_name:
                    case LogicalDataTypeNameEnum.DATETIME:
                        cell_value = py_value.isoformat()
                    case (
                        LogicalDataTypeNameEnum.BOOLEAN
                        | LogicalDataTypeNameEnum.INTEGER
                        | LogicalDataTypeNameEnum.FLOAT
                        | LogicalDataTypeNameEnum.STRING
                        | LogicalDataTypeNameEnum.DECIMAL
                        | LogicalDataTypeNameEnum.UUID
                    ):
                        cell_value = f"{py_value}"
                    case _:
                        raise ValueError(
                            f"Unsupported logical_data_type_name: {logical_column.logical_data_type_name}"
                        )
                entity_values[
                    logical_column.raw_index - self.preserved_raw_column_count
                ] = cell_value
            rows.append(entity_values)
        return rows
