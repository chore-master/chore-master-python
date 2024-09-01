from sqlalchemy import Column
from sqlalchemy.sql import func

from modules.database.sqlalchemy.types import DateTime, String


def get_base_columns():
    return [
        Column("reference", String, primary_key=True, index=True, nullable=False),
        Column("create_time", DateTime, index=True, server_default=func.now()),
        Column(
            "update_time",
            DateTime,
            index=True,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    ]
