from sqlalchemy import Column, Table
from sqlalchemy.orm import configure_mappers, registry

from apps.chore_master_api.end_user_database.tables.base import get_base_columns
from apps.chore_master_api.models.some_module import SomeEntity
from modules.database.sqlalchemy import types


class EndUserORM:
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

        configure_mappers()
