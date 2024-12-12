import os
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.script.base import Script
from sqlalchemy import Column, NullPool, Table, event, inspect
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema, MetaData

from modules.database.sqlalchemy import types


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
        conn_args = {
            "future": True,
            "poolclass": NullPool,
        }
        if origin.startswith("postgresql"):
            conn_args.update(
                {
                    "isolation_level": "READ COMMITTED",
                    # https://github.com/sqlalchemy/sqlalchemy/discussions/10246#discussioncomment-6961258
                    "connect_args": {
                        "prepared_statement_name_func": lambda: "",
                        "statement_cache_size": 0,
                    },
                }
            )
        elif origin.startswith("sqlite"):
            conn_args.update(
                {
                    "isolation_level": "SERIALIZABLE",
                }
            )
        self._conn_args = conn_args
        self._async_engine = create_async_engine(origin, **self._conn_args)
        # self._metadata = self.get_metadata(schema_name=self.schema_name)
        # self._metadata = metadata

    @property
    def origin(self) -> str:
        return self._origin

    @property
    def conn_args(self) -> dict:
        return self._conn_args

    # @property
    # def schema_name(self) -> str:
    #     # return self._schema_name
    #     return self._metadata.schema

    # @property
    # def metadata(self) -> MetaData:
    #     return self._metadata

    def get_async_session(self) -> sessionmaker[AsyncSession]:
        async_session_factory = sessionmaker(
            self._async_engine, class_=AsyncSession, autoflush=False
        )
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

    async def drop_tables(self, metadata: MetaData):
        Table(
            "alembic_version",
            metadata,
            Column("version_num", types.String, nullable=False),
        )
        async with self._async_engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)

    # async def create_schema(self):
    #     async with self._async_engine.begin() as conn:
    #         await conn.execute(CreateSchema(self.schema_name))


class SchemaMigration:
    @staticmethod
    def get_script_dict(script: Script) -> dict:
        return {
            "doc": script.doc,
            "down_revision": script.down_revision,
            "is_base": script.is_base,
            "is_branch_point": script.is_branch_point,
            "is_head": script.is_head,
            "is_merge_point": script.is_merge_point,
            "revision": script.revision,
            "path": script.path,
        }

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
        alembic_cfg.attributes["injected_conn_args"] = self._db.conn_args
        return alembic_cfg

    def get_version_location(self) -> str:
        return self._version_dir

    def generate_revision(self, metadata: MetaData) -> list[Script]:
        alembic_cfg = self.create_alembic_config(metadata)
        script = command.revision(alembic_cfg, autogenerate=True)
        if isinstance(script, Script):
            return [script]
        return script

    def all_revisions(self, metadata: MetaData) -> list[dict]:
        alembic_cfg = self.create_alembic_config(metadata)
        script = ScriptDirectory.from_config(alembic_cfg)
        return [
            self.get_script_dict(script)
            for script in script.walk_revisions(base="base", head="heads")
        ]

    def applied_revision(self, metadata: MetaData) -> Optional[dict]:
        current_revision = None

        def _get_current_revision(_rev, context) -> tuple[str, ...]:
            nonlocal current_revision
            current_revision = context.get_current_heads()
            return []

        alembic_cfg = self.create_alembic_config(metadata)
        script = ScriptDirectory.from_config(alembic_cfg)

        with EnvironmentContext(
            alembic_cfg, script, fn=_get_current_revision, dont_mutate=True
        ):
            script.run_env()
        current_script: Optional[Script] = next(
            iter(script.get_all_current(current_revision)), None
        )
        if current_script is None:
            return None
        return self.get_script_dict(current_script)

    def upgrade(self, metadata: MetaData, revision: str = "head"):
        alembic_cfg = self.create_alembic_config(metadata)
        command.upgrade(alembic_cfg, revision)

    def downgrade(self, metadata: MetaData, revision: str = "-1"):
        alembic_cfg = self.create_alembic_config(metadata)
        command.downgrade(alembic_cfg, revision)
