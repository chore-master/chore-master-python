from modules.google_service.models.logical_sheet import (
    LogicalColumn,
    LogicalDataTypeNameEnum,
)


def get_base_logical_columns() -> list[LogicalColumn]:
    return [
        LogicalColumn(
            logical_name="reference",
            logical_data_type_name=LogicalDataTypeNameEnum.UUID,
            logical_is_primary_key=True,
            logical_is_unique_key=True,
        ),
    ]
