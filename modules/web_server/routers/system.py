from fastapi import APIRouter

from modules.base.config import get_base_config
from modules.web_server.schemas.response import (
    HealthSchema,
    InspectSchema,
    ResponseSchema,
    StatusEnum,
)

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    name="Service Healthcheck",
    description="Provide a simple healthcheck of the service",
)
def get_liveness():
    return ResponseSchema[HealthSchema](
        status=StatusEnum.SUCCESS, data=HealthSchema(None)
    )


@router.get("/inspect")
def get_inspect():
    base_config = get_base_config()
    return ResponseSchema[InspectSchema](
        status=StatusEnum.SUCCESS,
        data=InspectSchema(
            env=base_config.ENV,
            service_name=base_config.SERVICE_NAME,
            component_name=base_config.COMPONENT_NAME,
            commit_short_sha=base_config.COMMIT_SHORT_SHA,
            commit_revision=base_config.COMMIT_REVISION,
        ),
    )
