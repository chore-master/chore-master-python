import asyncio

import nest_asyncio
from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

# from modules.database.config import get_config
# from modules.database.sa.registry import mapper_registry
from modules.database.relational_database import RelationalDatabase

nest_asyncio.apply()

# from modules.database.tables.data_version import data_version_table

# from logging.config import fileConfig


# db_config = get_config()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
db: RelationalDatabase = config.attributes["injected_db"]
target_metadata = db.metadata
schema_name = db.schema_name

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# 魔改區開始


def include_object(object, name, type_, reflected, compare_to):
    #     if type_ == "table" and name in {"alembic_version", data_version_table.name}:
    #         return False
    return True


# 魔改區結束


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def async_run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        if connectable.dialect.name == "postgresql":
            # set search path on the connection, which ensures that
            # PostgreSQL will emit all CREATE / ALTER / DROP statements
            # in terms of this schema by default
            # https://stackoverflow.com/questions/69490450/sqlalchemy-v1-4-objectnotexecutableerror-when-executing-any-sql-query-using-asyn
            await connection.execute(text("set search_path to %s" % schema_name))

        # make use of non-supported SQLAlchemy attribute to ensure
        # the dialect reflects tables in terms of the current tenant name
        connection.dialect.default_schema_name = schema_name

        def _run_migrations(connection):
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                # 魔改區開始
                # https://gist.github.com/h4/fc9b6d350544ff66491308b535762fee
                version_table_schema=schema_name,
                include_schemas=False,
                include_object=include_object,
                compare_type=True,
                compare_server_default=True,
                # 魔改區結束
            )

            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(_run_migrations)
        await connection.commit()
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(async_run_migrations_online())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
