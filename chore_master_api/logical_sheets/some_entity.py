from modules.google_service.mixin import get_base_logical_columns
from modules.google_service.models.logical_sheet import (
    LogicalColumn,
    LogicalDataTypeNameEnum,
    LogicalSheet,
)

some_entity_logical_sheet = LogicalSheet(
    logical_name="some_entity",
    logical_columns=[
        *get_base_logical_columns(),
        LogicalColumn(
            logical_name="a",
            logical_data_type_name=LogicalDataTypeNameEnum.BOOLEAN,
        ),
        LogicalColumn(
            logical_name="b",
            logical_data_type_name=LogicalDataTypeNameEnum.INTEGER,
        ),
        LogicalColumn(
            logical_name="c",
            logical_data_type_name=LogicalDataTypeNameEnum.FLOAT,
        ),
        LogicalColumn(
            logical_name="d",
            logical_data_type_name=LogicalDataTypeNameEnum.DECIMAL,
        ),
        LogicalColumn(
            logical_name="e",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
        LogicalColumn(
            logical_name="f",
            logical_data_type_name=LogicalDataTypeNameEnum.DATETIME,
        ),
    ],
)