import contextlib
from datetime import timedelta
from decimal import Decimal
from typing import AsyncGenerator, NewType, Optional

from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions, TypeCodec, TypeRegistry
from bson.decimal128 import Decimal128
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorDatabase,
)
from pymongo.write_concern import WriteConcern

AsyncMongoDB = NewType("AsyncMongoDB", AsyncIOMotorDatabase)


class DecimalCodec(TypeCodec):
    python_type = Decimal
    bson_type = Decimal128

    def transform_bson(self, value: Decimal128) -> Decimal:
        return value.to_decimal()

    def transform_python(self, value: Decimal) -> Decimal128:
        return Decimal128(value)


class TimedeltaCodec(TypeCodec):
    python_type = timedelta
    bson_type = dict

    def transform_bson(self, value: dict) -> timedelta | dict:
        t = value.get("__type__")
        if t is None:
            return value
        elif t == "timedelta":
            return timedelta(
                days=value["days"],
                seconds=value["seconds"],
                microseconds=value["microseconds"],
            )

    def transform_python(self, value: timedelta) -> dict:
        return {
            "__type__": "timedelta",
            "days": value.days,
            "seconds": value.seconds,
            "microseconds": value.microseconds,
        }


class AsyncMongoClient:
    def __init__(
        self,
        host: Optional[str] = None,
        min_pool_size: Optional[int] = None,
        max_pool_size: Optional[int] = None,
    ):
        self._client = AsyncIOMotorClient(
            host,
            readPreference="secondaryPreferred",
            retryWrites=True,
            uuidRepresentation="standard",
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
        )
        type_registry = TypeRegistry(type_codecs=[DecimalCodec(), TimedeltaCodec()])
        self.codec_options = CodecOptions(
            uuid_representation=UuidRepresentation.STANDARD, type_registry=type_registry
        )

    def close(self):
        self._client.close()

    async def admin_command(self, *args, **kwargs) -> dict:
        return await self._client.admin.command(*args, **kwargs)

    def get_database(self, database_name: str) -> AsyncMongoDB:
        write_concern = WriteConcern(w=1, j=True, wtimeout=10000)
        return self._client.get_database(
            database_name, codec_options=self.codec_options, write_concern=write_concern
        )

    async def drop_database(self, database_name: str):
        await self._client.drop_database(database_name)

    @contextlib.asynccontextmanager
    async def start_transaction(
        self,
    ) -> AsyncGenerator[AsyncIOMotorClientSession, None]:
        async with await self._client.start_session() as session:
            with session.start_transaction():
                yield session
