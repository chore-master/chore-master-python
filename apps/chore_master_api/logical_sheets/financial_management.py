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

asset_logical_sheet = LogicalSheet(
    logical_name="asset",
    logical_columns=[
        *get_base_logical_columns(),
        LogicalColumn(
            logical_name="symbol",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
    ],
)


net_value_logical_sheet = LogicalSheet(
    logical_name="net_value",
    logical_columns=[
        *get_base_logical_columns(),
        LogicalColumn(
            logical_name="account_reference",
            logical_data_type_name=LogicalDataTypeNameEnum.UUID,
        ),
        LogicalColumn(
            logical_name="amount",
            logical_data_type_name=LogicalDataTypeNameEnum.DECIMAL,
        ),
        LogicalColumn(
            logical_name="settlement_asset_reference",
            logical_data_type_name=LogicalDataTypeNameEnum.UUID,
        ),
        LogicalColumn(
            logical_name="settled_time",
            logical_data_type_name=LogicalDataTypeNameEnum.DATETIME,
        ),
    ],
)

bill_logical_sheet = LogicalSheet(
    logical_name="bill",
    logical_columns=[
        *get_base_logical_columns(),
        LogicalColumn(
            logical_name="account_reference",
            logical_data_type_name=LogicalDataTypeNameEnum.UUID,
        ),
        LogicalColumn(
            logical_name="business_type",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
        LogicalColumn(
            logical_name="accounting_type",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
        LogicalColumn(
            logical_name="amount_change",
            logical_data_type_name=LogicalDataTypeNameEnum.DECIMAL,
        ),
        LogicalColumn(
            logical_name="asset_reference",
            logical_data_type_name=LogicalDataTypeNameEnum.UUID,
        ),
        LogicalColumn(
            logical_name="order_reference",
            logical_data_type_name=LogicalDataTypeNameEnum.STRING,
        ),
        LogicalColumn(
            logical_name="billed_time",
            logical_data_type_name=LogicalDataTypeNameEnum.DATETIME,
        ),
    ],
)
