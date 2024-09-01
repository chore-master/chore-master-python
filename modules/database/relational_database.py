import os
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.script.base import Script
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema, MetaData


class RelationalDatabase:
    @staticmethod
    def create_metadata(schema_name: Optional[str] = None) -> MetaData:
        if schema_name is None or schema_name == "":
            convention = {
                "ix": "ix_%(column_0_label)s",
                "uq": "uq_%(table_name)s_%(column_0_name)s",
                "ck": "ck_%(table_name)s_%(constraint_name)s",
                "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                "pk": "pk_%(table_name)s",
            }
            return MetaData(naming_convention=convention)
        else:
            convention = {
                "ix": f"ix_{schema_name}_%(column_0_label)s",
                "uq": f"uq_{schema_name}_%(table_name)s_%(column_0_name)s",
                "ck": f"ck_{schema_name}_%(table_name)s_%(constraint_name)s",
                "fk": f"fk_{schema_name}_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                "pk": f"pk_{schema_name}_%(table_name)s",
            }
            return MetaData(schema=schema_name, naming_convention=convention)

    @staticmethod
    def create_mapper_registry(metadata: MetaData) -> registry:
        return registry(metadata=metadata)

    # @staticmethod
    # def get_schema_names(conn: AsyncConnection):
    #     inspector = inspect(conn)
    #     return inspector.get_schema_names()

    def __init__(self, origin: str):
        self._origin = origin
        # if schema_name == "":
        #     schema_name = None
        # self._schema_name = schema_name
        self._async_engine = create_async_engine(
            origin,
            # isolation_level="READ COMMITTED",
            isolation_level="SERIALIZABLE",
            future=True,
        )
        # self._metadata = self.get_metadata(schema_name=self.schema_name)
        # self._metadata = metadata

    @property
    def origin(self) -> str:
        return self._origin

    # @property
    # def schema_name(self) -> str:
    #     # return self._schema_name
    #     return self._metadata.schema

    # @property
    # def metadata(self) -> MetaData:
    #     return self._metadata

    def get_async_session(self) -> sessionmaker[AsyncSession]:
        async_session_factory = sessionmaker(self._async_engine, class_=AsyncSession)
        return async_session_factory

    # async def reflect_metadata(self):
    #     self.metadata = MetaData(schema=self.schema_name)
    #     async with self._async_engine.begin() as conn:
    #         await conn.run_sync(self.metadata.reflect)

    # async def has_table(self, tablename: str) -> bool:
    #     def _has_table(conn):
    #         inspector = inspect(conn)
    #         return inspector.has_table(tablename)

    #     async with self._async_engine.begin() as conn:
    #         r = await conn.run_sync(_has_table)
    #         return r

    # async def reset_schema(self):
    #     async with self._async_engine.begin() as conn:
    #         schema_names = await conn.run_sync(self.get_schema_names)
    #         if self.schema_name in schema_names:
    #             await self.drop_tables()
    #             await self.drop_schema()
    #     await self.create_schema()

    # async def drop_schema(self):
    #     async with self._async_engine.begin() as conn:
    #         await conn.execute(DropSchema(self.schema_name))

    # async def drop_tables(self):
    #     reflected_metadata = MetaData(schema=self.schema_name)
    #     async with self._async_engine.begin() as conn:
    #         await conn.run_sync(reflected_metadata.reflect)
    #         await conn.run_sync(reflected_metadata.drop_all)

    # async def create_schema(self):
    #     async with self._async_engine.begin() as conn:
    #         await conn.execute(CreateSchema(self.schema_name))


class SchemaMigration:
    def __init__(
        self, database: RelationalDatabase, version_dir: str, alembic_dir: str
    ):
        self._db = database
        self._version_dir = version_dir
        self._alembic_dir = alembic_dir

    def create_alembic_config(self, metadata: MetaData) -> Config:
        # https://alembic.sqlalchemy.org/en/latest/api/config.html
        alembic_cfg = Config()
        alembic_cfg.set_main_option("sqlalchemy.url", self._db.origin)
        alembic_cfg.set_main_option("script_location", self._alembic_dir)
        alembic_cfg.set_main_option(
            "file_template",
            "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d_%%(minute).2d_%%(second).2d_%%(rev)s",
        )
        version_location = self.get_version_location()
        if not os.path.exists(version_location):
            os.makedirs(version_location)
        alembic_cfg.set_main_option("version_locations", version_location)
        alembic_cfg.attributes["injected_metadata"] = metadata
        return alembic_cfg

    def get_version_location(self) -> str:
        return self._version_dir

    def generate_revision(self, metadata: MetaData) -> list[Script]:
        alembic_cfg = self.create_alembic_config(metadata)
        script = command.revision(alembic_cfg, autogenerate=True)
        if isinstance(script, Script):
            return [script]
        return script

    def upgrade(self, metadata: MetaData, revision: str = "head"):
        alembic_cfg = self.create_alembic_config(metadata)
        command.upgrade(alembic_cfg, revision)

    def downgrade(self, metadata: MetaData, revision: str = "-1"):
        alembic_cfg = self.create_alembic_config(metadata)
        command.downgrade(alembic_cfg, revision)
