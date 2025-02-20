from sqlalchemy import Column, Table
from sqlalchemy.orm import configure_mappers, registry, relationship

from apps.chore_master_api.end_user_space.models import integration
from apps.chore_master_api.end_user_space.models.financial_management import (
    Account,
    Asset,
    Bill,
    NetValue,
)
from apps.chore_master_api.end_user_space.models.some_module import SomeEntity
from apps.chore_master_api.end_user_space.tables.base import get_base_columns
from modules.database.sqlalchemy import types


class Mapper:
    def __init__(self, mapper_registry: registry):
        self._mapper_registry = mapper_registry
        self._metadata = self._mapper_registry.metadata

    def map_models_to_tables(self):
        some_module_some_entity_table = Table(
            "some_module_some_entity",
            self._metadata,
            *get_base_columns(),
            Column("a", types.Boolean, nullable=False),
            Column("b", types.Integer, nullable=False),
            Column("c", types.Float, nullable=False),
            Column("d", types.Decimal, nullable=False),
            Column("e", types.String, nullable=False),
            Column("f", types.DateTime, nullable=False),
            Column("g", types.String, nullable=False),
            Column("h", types.Integer, nullable=True),
            Column("i", types.JSON, nullable=True),
        )
        if getattr(SomeEntity, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                SomeEntity, some_module_some_entity_table
            )

        integration_resource_table = Table(
            "integration_resource",
            self._metadata,
            *get_base_columns(),
            Column("end_user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("discriminator", types.String, nullable=False),
            Column("value", types.JSON, nullable=False),
        )
        if getattr(integration.Resource, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                integration.Resource, integration_resource_table
            )

        financial_management_account_table = Table(
            "financial_management_account",
            self._metadata,
            *get_base_columns(),
            Column("name", types.String, nullable=False),
        )
        if getattr(Account, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                Account, financial_management_account_table
            )

        financial_management_asset_table = Table(
            "financial_management_asset",
            self._metadata,
            *get_base_columns(),
            Column("symbol", types.String, nullable=False),
        )
        if getattr(Asset, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                Asset, financial_management_asset_table
            )

        financial_management_net_value_table = Table(
            "financial_management_net_value",
            self._metadata,
            *get_base_columns(),
            Column("account_reference", types.String, nullable=False),
            Column("amount", types.Decimal, nullable=False),
            Column("settlement_asset_reference", types.String, nullable=False),
            Column("settled_time", types.DateTime, nullable=False),
        )
        if getattr(NetValue, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                NetValue,
                financial_management_net_value_table,
                properties={
                    "account": relationship(
                        "Account",
                        foreign_keys=[
                            financial_management_net_value_table.columns.account_reference
                        ],
                        primaryjoin="NetValue.account_reference == Account.reference",
                    ),
                    "settlement_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            financial_management_net_value_table.columns.settlement_asset_reference
                        ],
                        primaryjoin="NetValue.settlement_asset_reference == Asset.reference",
                    ),
                },
            )

        financial_management_bill_table = Table(
            "financial_management_bill",
            self._metadata,
            *get_base_columns(),
            Column("account_reference", types.String, nullable=False),
            Column("business_type", types.String, nullable=False),
            Column("accounting_type", types.String, nullable=False),
            Column("amount_change", types.Decimal, nullable=False),
            Column("asset_reference", types.String, nullable=False),
            Column("order_reference", types.String, nullable=True),
            Column("billed_time", types.DateTime, nullable=True),
        )
        if getattr(Bill, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                Bill, financial_management_bill_table
            )

        configure_mappers()
