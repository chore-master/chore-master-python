from sqlalchemy import Column, Table
from sqlalchemy.orm import configure_mappers, registry, relationship

from apps.chore_master_api.end_user_space.models import (
    finance,
    identity,
    integration,
    some_module,
)
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
        if getattr(some_module.SomeEntity, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                some_module.SomeEntity, some_module_some_entity_table
            )

        identity_user_table = Table(
            "identity_user",
            self._metadata,
            *get_base_columns(),
            Column("name", types.String, nullable=False),
            Column("username", types.String, nullable=False),
            Column("password", types.String, nullable=False),
        )
        if getattr(identity.User, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(identity.User, identity_user_table)

        identity_role_table = Table(
            "identity_role",
            self._metadata,
            *get_base_columns(),
            Column("symbol", types.String, nullable=False),
        )
        if getattr(identity.Role, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(identity.Role, identity_role_table)

        identity_user_role_table = Table(
            "identity_user_role",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("role_reference", types.String, nullable=False),
        )
        if getattr(identity.UserRole, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                identity.UserRole,
                identity_user_role_table,
                properties={
                    "user": relationship(
                        "User",
                        foreign_keys=[identity_user_role_table.columns.user_reference],
                        primaryjoin="UserRole.user_reference == User.reference",
                        backref="user_roles",
                    ),
                    "role": relationship(
                        "Role",
                        foreign_keys=[identity_user_role_table.columns.role_reference],
                        primaryjoin="UserRole.role_reference == Role.reference",
                        backref="user_roles",
                    ),
                },
            )

        identity_user_session_table = Table(
            "identity_user_session",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("user_agent", types.String, nullable=False),
            Column("is_active", types.Boolean, nullable=False),
            Column("expired_time", types.DateTime, nullable=False),
            Column("deactivated_time", types.DateTime, nullable=True),
        )
        if getattr(identity.UserSession, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                identity.UserSession,
                identity_user_session_table,
                properties={
                    "user": relationship(
                        "User",
                        foreign_keys=[
                            identity_user_session_table.columns.user_reference
                        ],
                        primaryjoin="UserSession.user_reference == User.reference",
                    )
                },
            )

        integration_operator_table = Table(
            "integration_operator",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("discriminator", types.String, nullable=False),
            Column("value", types.JSON, nullable=False),
        )
        if getattr(integration.Operator, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                integration.Operator, integration_operator_table
            )

        finance_asset_table = Table(
            "finance_asset",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("symbol", types.String, nullable=False),
            Column("decimals", types.Integer, nullable=False),
            Column("is_settleable", types.Boolean, nullable=False),
        )
        if getattr(finance.Asset, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(finance.Asset, finance_asset_table)

        finance_account_table = Table(
            "finance_account",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("opened_time", types.DateTime, nullable=False),
            Column("closed_time", types.DateTime, nullable=True),
            Column("ecosystem_type", types.String, nullable=False),
            Column("settlement_asset_reference", types.String, nullable=False),
        )
        if getattr(finance.Account, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Account, finance_account_table
            )

        finance_balance_sheet_table = Table(
            "finance_balance_sheet",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("balanced_time", types.DateTime, nullable=False),
        )
        if getattr(finance.BalanceSheet, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.BalanceSheet, finance_balance_sheet_table
            )

        finance_balance_entry_table = Table(
            "finance_balance_entry",
            self._metadata,
            *get_base_columns(),
            Column("balance_sheet_reference", types.String, nullable=False),
            Column("account_reference", types.String, nullable=False),
            Column("amount", types.Integer, nullable=False),
        )
        if getattr(finance.BalanceEntry, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.BalanceEntry,
                finance_balance_entry_table,
                properties={
                    "balance_sheet": relationship(
                        "BalanceSheet",
                        foreign_keys=[
                            finance_balance_entry_table.columns.balance_sheet_reference
                        ],
                        primaryjoin="BalanceEntry.balance_sheet_reference == BalanceSheet.reference",
                        backref="balance_entries",
                    )
                },
            )

        finance_instrument_table = Table(
            "finance_instrument",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("quantity_decimals", types.Integer, nullable=False),
            Column("price_decimals", types.Integer, nullable=False),
            Column("instrument_type", types.String, nullable=False),
            Column("base_asset_reference", types.String, nullable=True),
            Column("quote_asset_reference", types.String, nullable=True),
            Column("settlement_asset_reference", types.String, nullable=True),
            Column("underlying_asset_reference", types.String, nullable=True),
            Column("staking_asset_reference", types.String, nullable=True),
            Column("yielding_asset_reference", types.String, nullable=True),
        )
        if getattr(finance.Instrument, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Instrument,
                finance_instrument_table,
                properties={
                    "base_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            finance_instrument_table.columns.base_asset_reference
                        ],
                        primaryjoin="Instrument.base_asset_reference == Asset.reference",
                    ),
                    "quote_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            finance_instrument_table.columns.quote_asset_reference
                        ],
                        primaryjoin="Instrument.quote_asset_reference == Asset.reference",
                    ),
                    "settlement_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            finance_instrument_table.columns.settlement_asset_reference
                        ],
                        primaryjoin="Instrument.settlement_asset_reference == Asset.reference",
                    ),
                    "underlying_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            finance_instrument_table.columns.underlying_asset_reference
                        ],
                        primaryjoin="Instrument.underlying_asset_reference == Asset.reference",
                    ),
                    "staking_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            finance_instrument_table.columns.staking_asset_reference
                        ],
                        primaryjoin="Instrument.staking_asset_reference == Asset.reference",
                    ),
                    "yielding_asset": relationship(
                        "Asset",
                        foreign_keys=[
                            finance_instrument_table.columns.yielding_asset_reference
                        ],
                        primaryjoin="Instrument.yielding_asset_reference == Asset.reference",
                    ),
                },
            )

        finance_portfolio_table = Table(
            "finance_portfolio",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("description", types.String, nullable=True),
        )
        if getattr(finance.Portfolio, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Portfolio, finance_portfolio_table
            )

        finance_ledger_entry_table = Table(
            "finance_ledger_entry",
            self._metadata,
            *get_base_columns(),
            Column("portfolio_reference", types.String, nullable=False),
            Column("instrument_reference", types.String, nullable=False),
            Column("entry_type", types.String, nullable=False),
            Column("source_type", types.String, nullable=False),
            Column("quantity", types.Integer, nullable=False),
            Column("price", types.Integer, nullable=False),
            Column("entry_time", types.DateTime, nullable=False),
        )
        if getattr(finance.LedgerEntry, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.LedgerEntry, finance_ledger_entry_table
            )

        finance_fee_entry_table = Table(
            "finance_fee_entry",
            self._metadata,
            *get_base_columns(),
            Column("ledger_entry_reference", types.String, nullable=False),
            Column("fee_type", types.String, nullable=False),
            Column("amount", types.Integer, nullable=False),
            Column("asset_reference", types.String, nullable=False),
        )
        if getattr(finance.FeeEntry, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.FeeEntry, finance_fee_entry_table
            )

        # financial_management_account_table = Table(
        #     "financial_management_account",
        #     self._metadata,
        #     *get_base_columns(),
        #     Column("name", types.String, nullable=False),
        # )
        # if getattr(Account, "_sa_class_manager", None) is None:
        #     self._mapper_registry.map_imperatively(
        #         Account, financial_management_account_table
        #     )

        # financial_management_asset_table = Table(
        #     "financial_management_asset",
        #     self._metadata,
        #     *get_base_columns(),
        #     Column("symbol", types.String, nullable=False),
        # )
        # if getattr(Asset, "_sa_class_manager", None) is None:
        #     self._mapper_registry.map_imperatively(
        #         Asset, financial_management_asset_table
        #     )

        # financial_management_net_value_table = Table(
        #     "financial_management_net_value",
        #     self._metadata,
        #     *get_base_columns(),
        #     Column("account_reference", types.String, nullable=False),
        #     Column("amount", types.Decimal, nullable=False),
        #     Column("settlement_asset_reference", types.String, nullable=False),
        #     Column("settled_time", types.DateTime, nullable=False),
        # )
        # if getattr(NetValue, "_sa_class_manager", None) is None:
        #     self._mapper_registry.map_imperatively(
        #         NetValue,
        #         financial_management_net_value_table,
        #         properties={
        #             "account": relationship(
        #                 "Account",
        #                 foreign_keys=[
        #                     financial_management_net_value_table.columns.account_reference
        #                 ],
        #                 primaryjoin="NetValue.account_reference == Account.reference",
        #             ),
        #             "settlement_asset": relationship(
        #                 "Asset",
        #                 foreign_keys=[
        #                     financial_management_net_value_table.columns.settlement_asset_reference
        #                 ],
        #                 primaryjoin="NetValue.settlement_asset_reference == Asset.reference",
        #             ),
        #         },
        #     )

        # financial_management_bill_table = Table(
        #     "financial_management_bill",
        #     self._metadata,
        #     *get_base_columns(),
        #     Column("account_reference", types.String, nullable=False),
        #     Column("business_type", types.String, nullable=False),
        #     Column("accounting_type", types.String, nullable=False),
        #     Column("amount_change", types.Decimal, nullable=False),
        #     Column("asset_reference", types.String, nullable=False),
        #     Column("order_reference", types.String, nullable=True),
        #     Column("billed_time", types.DateTime, nullable=True),
        # )
        # if getattr(Bill, "_sa_class_manager", None) is None:
        #     self._mapper_registry.map_imperatively(
        #         Bill, financial_management_bill_table
        #     )

        configure_mappers()
