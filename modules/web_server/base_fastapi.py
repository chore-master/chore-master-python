from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from modules.base.exceptions import BaseError
from modules.base.schemas.system import BaseConfigSchema
from modules.web_server.exceptions import (
    BadRequestError,
    PermissionDeniedError,
    UnauthorizedError,
)
from modules.web_server.routers import system
from modules.web_server.schemas.response import ErrorSchema, ResponseSchema, StatusEnum


class BaseFastAPI(FastAPI):
    def __init__(
        self,
        base_config: BaseConfigSchema,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            version=(
                base_config.COMMIT_REVISION or base_config.COMMIT_SHORT_SHA or "N/A"
            ),
            **kwargs,
        )
        self.include_router(system.router)
        self.add_error_handlers()

    def add_error_handlers(self):
        @self.exception_handler(RequestValidationError)
        async def request_validation_error_handler(
            request: Request, exc: RequestValidationError
        ):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED,
                    data=ErrorSchema(
                        message="Invalid request format",
                        detail=jsonable_encoder(exc.errors()),
                    ),
                ).model_dump(),
            )

        @self.exception_handler(404)
        async def not_found_error_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED,
                    data=ErrorSchema(message=f"{exc.detail}"),
                ).model_dump(),
            )

        @self.exception_handler(BadRequestError)
        async def bad_request_error_handler(req: Request, exc: BadRequestError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED, data=ErrorSchema(message=f"{exc}")
                ).model_dump(),
            )

        @self.exception_handler(UnauthorizedError)
        async def unauthorized_error_handler(req: Request, exc: UnauthorizedError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED, data=ErrorSchema(message=f"{exc}")
                ).model_dump(),
            )

        @self.exception_handler(PermissionDeniedError)
        async def permission_denied_error_handler(
            req: Request, exc: PermissionDeniedError
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED, data=ErrorSchema(message=f"{exc}")
                ).model_dump(),
            )

        @self.exception_handler(BaseError)
        async def base_error_handler(req: Request, exc: BaseError):
            print(f"{exc}", flush=True)  # log error intentionally
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED,
                    data=ErrorSchema(message="Internal Server Error"),
                ).model_dump(),
            )

        @self.exception_handler(Exception)
        async def uncaught_error_handler(req: Request, exc: Exception):
            print(f"{exc}", flush=True)  # log error intentionally
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ResponseSchema[ErrorSchema](
                    status=StatusEnum.FAILED,
                    data=ErrorSchema(message="Internal Server Error"),
                ).model_dump(),
            )
