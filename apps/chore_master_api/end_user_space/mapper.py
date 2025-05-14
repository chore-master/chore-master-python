from sqlalchemy import Column, Table
from sqlalchemy.orm import configure_mappers, registry, relationship

from apps.chore_master_api.end_user_space.models import (
    finance,
    identity,
    integration,
    some_module,
    trace,
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
            Column("email", types.String, nullable=True),
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

        trace_quota_table = Table(
            "trace_quota",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("limit", types.Integer, nullable=False),
            Column("used", types.Integer, nullable=False),
        )
        if getattr(trace.Quota, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(trace.Quota, trace_quota_table)

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
            Column("settlement_asset_reference", types.String, nullable=False),
        )
        if getattr(finance.Account, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Account, finance_account_table
            )

        finance_price_table = Table(
            "finance_price",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("base_asset_reference", types.String, nullable=False),
            Column("quote_asset_reference", types.String, nullable=False),
            Column("value", types.String, nullable=False),
            Column("confirmed_time", types.DateTime, nullable=False),
        )
        if getattr(finance.Price, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(finance.Price, finance_price_table)

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
            Column("amount", types.String, nullable=False),
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

        finance_portfolio_table = Table(
            "finance_portfolio",
            self._metadata,
            *get_base_columns(),
            Column("user_reference", types.String, nullable=False),
            Column("name", types.String, nullable=False),
            Column("settlement_asset_reference", types.String, nullable=False),
            Column("description", types.String, nullable=True),
        )
        if getattr(finance.Portfolio, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Portfolio, finance_portfolio_table
            )

        finance_transaction_table = Table(
            "finance_transaction",
            self._metadata,
            *get_base_columns(),
            Column("portfolio_reference", types.String, nullable=False),
            Column("transacted_time", types.DateTime, nullable=False),
            Column("chain_id", types.String, nullable=True),
            Column("tx_hash", types.String, nullable=True),
            Column("remark", types.String, nullable=True),
        )
        if getattr(finance.Transaction, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Transaction, finance_transaction_table
            )

        finance_transfer_table = Table(
            "finance_transfer",
            self._metadata,
            *get_base_columns(),
            Column("transaction_reference", types.String, nullable=False),
            Column("flow_type", types.String, nullable=False),
            Column("asset_amount_change", types.String, nullable=False),
            Column("asset_reference", types.String, nullable=False),
            Column("settlement_asset_amount_change", types.String, nullable=True),
            Column("remark", types.String, nullable=True),
        )
        if getattr(finance.Transfer, "_sa_class_manager", None) is None:
            self._mapper_registry.map_imperatively(
                finance.Transfer,
                finance_transfer_table,
                properties={
                    "transaction": relationship(
                        "Transaction",
                        foreign_keys=[
                            finance_transfer_table.columns.transaction_reference
                        ],
                        primaryjoin="Transfer.transaction_reference == Transaction.reference",
                        backref="transfers",
                    ),
                },
            )

        configure_mappers()
