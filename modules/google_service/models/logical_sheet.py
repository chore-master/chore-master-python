from __future__ import annotations

import json
from collections import namedtuple
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, NamedTuple, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from chore_master_api.models.base import Entity


class LogicalDataTypeNameEnum(str, Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    DATETIME = "DATETIME"
    DECIMAL = "DECIMAL"
    JSON = "JSON"
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

    @model_validator(mode="after")
    def ensure_value_deserializable(self) -> LogicalColumn:
        if (
            self.logical_data_type_name == LogicalDataTypeNameEnum.STRING
            and self.logical_is_nullable
        ):
            raise ValueError(
                f"Logical column `{self.logical_name}` cannot have STRING type and logical_is_nullable=True in the same time"
            )
        return self


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

    @model_validator(mode="after")
    def ensure_column_name_unique(self) -> LogicalSheet:
        logical_column_names_set = set()
        for col in self.logical_columns:
            if col.logical_name in logical_column_names_set:
                raise ValueError(f"Column name `{col.logical_name}` is duplicated")
            logical_column_names_set.add(col.logical_name)
        return self

    @property
    def preserved_raw_row_count(self) -> int:
        return len(self.preserved_raw_row_names._fields)

    @property
    def preserved_raw_column_count(self) -> int:
        return len(self.preserved_raw_column_names._fields)

    @property
    def logical_column_name_to_logical_column_map(self) -> Mapping[str, LogicalColumn]:
        return {c.logical_name: c for c in self.logical_columns}

    @staticmethod
    def cast_py_value_to_cell_value(
        py_value: Any, logical_column: LogicalColumn
    ) -> Any:
        if py_value is None:
            if not logical_column.logical_is_nullable:
                raise ValueError(
                    f"Non-nullable column {logical_column.logical_name} is None"
                )
            py_value = ""
        match logical_column.logical_data_type_name:
            case LogicalDataTypeNameEnum.DATETIME:
                cell_value = py_value.isoformat()
            case LogicalDataTypeNameEnum.JSON:
                cell_value = json.dumps(py_value)
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
        return cell_value

    @staticmethod
    def cast_cell_value_to_py_value(
        cell_value: Any, logical_column: LogicalColumn
    ) -> Any:
        if cell_value == "":
            if not logical_column.logical_is_nullable:
                raise ValueError(
                    f"Non-nullable column {logical_column.logical_name} is None"
                )
            else:
                return None
        match logical_column.logical_data_type_name:
            case LogicalDataTypeNameEnum.BOOLEAN:
                if cell_value == "True":
                    py_value = True
                elif cell_value == "False":
                    py_value = False
                else:
                    raise ValueError(f"Invalid boolean value: {cell_value}")
            case LogicalDataTypeNameEnum.INTEGER:
                py_value = int(cell_value)
            case LogicalDataTypeNameEnum.FLOAT:
                py_value = float(cell_value)
            case LogicalDataTypeNameEnum.STRING:
                py_value = cell_value
            case LogicalDataTypeNameEnum.DATETIME:
                py_value = datetime.fromisoformat(cell_value)
            case LogicalDataTypeNameEnum.DECIMAL:
                py_value = Decimal(cell_value)
            case LogicalDataTypeNameEnum.JSON:
                py_value = json.loads(cell_value)
            case LogicalDataTypeNameEnum.UUID:
                py_value = UUID(cell_value)
            case _:
                raise ValueError(
                    f"Unsupported logical_data_type_name: {logical_column.logical_data_type_name}"
                )
        return py_value

    def raw_rows_from_entities(self, entities: list[Entity]) -> list[list]:
        rows = []
        for entity in entities:
            entity_values = [None for _ in range(len(self.logical_columns))]
            for logical_column in self.logical_columns:
                py_value = getattr(entity, logical_column.logical_name)
                cell_value = self.cast_py_value_to_cell_value(
                    py_value=py_value, logical_column=logical_column
                )
                entity_values[
                    logical_column.raw_index - self.preserved_raw_column_count
                ] = cell_value
            rows.append(entity_values)
        return rows

    def match_rows(
        self, body_values: list[list], filter: dict, limit: int
    ) -> tuple[list[dict], list[int]]:
        filtering_logical_columns: list[LogicalColumn] = []
        non_filtering_logical_columns: list[LogicalColumn] = []
        for logical_column in self.logical_columns:
            if logical_column.logical_name in filter:
                filtering_logical_columns.append(logical_column)
            else:
                non_filtering_logical_columns.append(logical_column)

        matched_row_dicts = []
        matched_row_indices = []
        matched_count = 0
        max_row_count = max(len(column_series) for column_series in body_values)
        for row_index in range(max_row_count):
            row_dict = {}
            is_row_matched = True
            for logical_column in filtering_logical_columns:
                column_series = body_values[
                    logical_column.raw_index - self.preserved_raw_column_count
                ]
                cell_value = (
                    column_series[row_index] if row_index < len(column_series) else ""
                )
                py_value = self.cast_cell_value_to_py_value(
                    cell_value=cell_value, logical_column=logical_column
                )
                if py_value != filter[logical_column.logical_name]:
                    is_row_matched = False
                    break
                row_dict[logical_column.logical_name] = py_value
            if not is_row_matched:
                continue
            for logical_column in non_filtering_logical_columns:
                column_series = body_values[
                    logical_column.raw_index - self.preserved_raw_column_count
                ]
                cell_value = (
                    column_series[row_index] if row_index < len(column_series) else ""
                )
                py_value = self.cast_cell_value_to_py_value(
                    cell_value=cell_value, logical_column=logical_column
                )
                row_dict[logical_column.logical_name] = py_value
            matched_row_dicts.append(row_dict)
            matched_row_indices.append(row_index)
            limit += 1
            if matched_count >= limit:
                break
        return matched_row_dicts, matched_row_indices
