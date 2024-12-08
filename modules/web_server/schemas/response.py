from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, RootModel

from modules.base.schemas.system import EnvEnum

DataT = TypeVar("DataT")


class StatusEnum(int, Enum):
    SUCCESS = 0
    FAILED = 1


class MetadataSchema(BaseModel):
    class OffsetPagination(BaseModel):
        count: int

    offset_pagination: Optional[OffsetPagination] = None


class ResponseSchema(BaseModel, Generic[DataT]):
    status: StatusEnum
    data: DataT
    metadata: Optional[MetadataSchema] = None


class ErrorSchema(BaseModel):
    message: str
    detail: Optional[Any] = None


class HealthSchema(RootModel[None]):
    root: None


class InspectSchema(BaseModel):
    env: EnvEnum
    service_name: str
    component_name: str
    commit_short_sha: Optional[str] = None
    commit_revision: Optional[str] = None
