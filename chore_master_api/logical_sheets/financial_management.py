from modules.google_service.mixin import get_base_logical_columns
from modules.google_service.models.logical_sheet import (
    LogicalColumn,
    LogicalDataTypeNameEnum,
    LogicalSheet,
)

account_logical_sheet = LogicalSheet(
    logical_name="account",
    logical_columns=[
        *get_base_logical_columns(),
        LogicalColumn(
            logical_name="name",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
    ],
)


passbook_logical_sheet = LogicalSheet(
    logical_name="passbook",
    logical_columns=[
        *get_base_logical_columns(),
        LogicalColumn(
            logical_name="account_reference",
            logical_data_type_name=LogicalDataTypeNameEnum.UUID,
        ),
        LogicalColumn(
            logical_name="balance_amount",
            logical_data_type_name=LogicalDataTypeNameEnum.DECIMAL,
        ),
        LogicalColumn(
            logical_name="balance_symbol",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
        LogicalColumn(
            logical_name="created_time",
            logical_data_type_name=LogicalDataTypeNameEnum.DATETIME,
        ),
    ],
)
