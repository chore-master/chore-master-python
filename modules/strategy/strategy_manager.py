import asyncio
import ctypes
import inspect
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import Annotated, Any, Callable, Coroutine, Mapping, Optional, Type

import uvicorn
from fastapi import APIRouter, Response
from pydantic import BaseModel, create_model

from modules.base.config import get_base_config
from modules.strategy.base_strategy import BaseStrategy
from modules.strategy.config import get_strategy_manager_config
from modules.strategy.exceptions import StrategyManagerValidationError
from modules.strategy.schemas.request import StrategyCommandArgumentSchema
from modules.strategy.schemas.response import StrategyCommandResultSchema
from modules.web_server.base_fastapi import BaseFastAPI
from modules.web_server.schemas.response import ResponseSchema, StatusEnum


class StrategyManager:
    def __init__(self):
        self.strategy_manager_config = get_strategy_manager_config()
        self._strategy_name_to_strategy_map: Mapping[str, BaseStrategy] = {}
        self._strategy_name_to_strategy_thread_worker_map: Mapping[
            str, StrategyThreadWorker
        ] = {}
        self._http_server = StrategyManagerHTTPServer(
            on_invoke_strategy_command=self.on_invoke_strategy_command,
            on_revoke_strategy_command=self.on_revoke_strategy_command,
        )

    def run_http_server(self):
        self._http_server.serve(port=self.strategy_manager_config.HTTP_SERVER_PORT)

    def is_strategy_registered(self, strategy_name: str) -> bool:
        return strategy_name in self._strategy_name_to_strategy_map

    def register_strategy(
        self, strategy: BaseStrategy, strategy_name: Optional[str] = None
    ):
        self._require_strategy_not_registered(strategy_name)
        if strategy_name is None:
            strategy_name = strategy.__class__.__name__
        self._http_server.register_strategy(
            strategy_name=strategy_name, strategy=strategy
        )
        self._strategy_name_to_strategy_map[strategy_name] = strategy
        self._strategy_name_to_strategy_thread_worker_map[strategy_name] = (
            StrategyThreadWorker(strategy_name=strategy_name, strategy=strategy)
        )

    async def on_invoke_strategy_command(
        self,
        strategy_name: str,
        command_name: str,
        command_args: tuple,
        command_kwargs: dict,
        should_wait_for_result: bool,
    ) -> Any:
        self._require_strategy_command_not_invoked(
            strategy_name=strategy_name, command_name=command_name
        )
        strategy_thread_worker = self._strategy_name_to_strategy_thread_worker_map[
            strategy_name
        ]
        result = await strategy_thread_worker.invoke_command(
            command_name=command_name,
            command_args=command_args,
            command_kwargs=command_kwargs,
            should_wait_for_result=should_wait_for_result,
        )
        return result

    async def on_revoke_strategy_command(self, strategy_name: str, command_name: str):
        self._require_strategy_command_invoked(
            strategy_name=strategy_name, command_name=command_name
        )
        strategy_thread_worker = self._strategy_name_to_strategy_thread_worker_map[
            strategy_name
        ]
        await strategy_thread_worker.revoke_command(command_name=command_name)

    def _require_strategy_registered(self, strategy_name: str):
        if not self.is_strategy_registered(strategy_name=strategy_name):
            raise StrategyManagerValidationError(
                f"Strategy `{strategy_name}` is not registered"
            )

    def _require_strategy_not_registered(self, strategy_name: str):
        if self.is_strategy_registered(strategy_name=strategy_name):
            raise StrategyManagerValidationError(
                f"Strategy `{strategy_name}` is registered"
            )

    def _require_strategy_command_invoked(self, strategy_name: str, command_name: str):
        if not self._strategy_name_to_strategy_thread_worker_map[
            strategy_name
        ].is_command_invoked(command_name=command_name):
            raise StrategyManagerValidationError(
                f"Thread for `{strategy_name}.{command_name}` was not invoked"
            )

    def _require_strategy_command_not_invoked(
        self, strategy_name: str, command_name: str
    ):
        if self._strategy_name_to_strategy_thread_worker_map[
            strategy_name
        ].is_command_invoked(command_name=command_name):
            raise StrategyManagerValidationError(
                f"Thread for `{strategy_name}.{command_name}` already invoked"
            )


class StrategyThreadWorker:
    @staticmethod
    def _raise_exception_in_thread(thread_id: str, exception_type: Type[Exception]):
        # https://medium.com/ching-i/%E5%A4%9A%E5%9F%B7%E8%A1%8C%E7%B7%92-%E7%B5%82%E6%AD%A2%E5%9F%B7%E8%A1%8C%E7%B7%92%E7%9A%84%E6%96%B9%E6%B3%95-d9e50c180873
        """raises the exception, performs cleanup if needed"""
        thread_id = ctypes.c_long(thread_id)
        if not inspect.isclass(exception_type):
            exception_type = type(exception_type)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(exception_type)
        )
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            """
            if it returns a number greater than one, you’re in
            trouble, # and you should call it again with exc=NULL to
            revert the effect
            """
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def __init__(self, strategy_name: str, strategy: BaseStrategy):
        self._strategy_name = strategy_name
        self._strategy = strategy
        self._command_name_to_thread_map: Mapping[str, Thread] = {}
        self._command_name_to_thread_result_map: Mapping[str, Any] = {}

    def is_command_invoked(self, command_name: str) -> bool:
        return not self._command_name_to_thread_map.get(command_name) is None

    async def invoke_command(
        self,
        command_name: str,
        command_args: tuple,
        command_kwargs: dict,
        should_wait_for_result: bool,
    ) -> Any:
        thread = Thread(
            target=self._thread_entrypoint,
            args=(command_name, command_args, command_kwargs),
            name=f"{self._strategy_name}.{command_name}",
        )
        self._command_name_to_thread_map[command_name] = thread
        thread.start()
        if should_wait_for_result:
            future = asyncio.get_event_loop().run_in_executor(None, thread.join)
            await future
            if command_name in self._command_name_to_thread_result_map:
                result = self._command_name_to_thread_result_map.pop(command_name)
            else:
                result = StrategyManagerValidationError("Thread was interrupted")
            return result

    async def revoke_command(self, command_name: str):
        thread = self._command_name_to_thread_map.get(command_name)
        if thread is None:
            return
        self._raise_exception_in_thread(
            thread_id=thread.ident, exception_type=SystemExit
        )
        thread.join()
        if command_name in self._command_name_to_thread_map:
            del self._command_name_to_thread_map[command_name]

    def _thread_entrypoint(
        self, command_name: str, command_args: tuple, command_kwargs: dict
    ):
        command = getattr(self._strategy, command_name)
        is_async_command = asyncio.iscoroutinefunction(command)
        is_sync_command = inspect.ismethod(command)
        raised_exception = None
        if is_async_command:
            event_loop = asyncio.new_event_loop()
            try:
                coroutine = command(*command_args, **command_kwargs)
                result = event_loop.run_until_complete(coroutine)
                self._command_name_to_thread_result_map[command_name] = result
            except SystemExit:
                event_loop.close()
            except Exception as exc:
                raised_exception = exc
        elif is_sync_command:
            try:
                result = command(*command_args, **command_kwargs)
                self._command_name_to_thread_result_map[command_name] = result
            except SystemExit:
                pass
            except Exception as exc:
                raised_exception = exc
        else:
            raise NotImplementedError
        del self._command_name_to_thread_map[command_name]
        if raised_exception is not None:
            self._command_name_to_thread_result_map[command_name] = raised_exception
            raise raised_exception


class StrategyManagerHTTPServer:
    class ResponseType(Enum):
        NO_WAIT = "NO_WAIT"
        JSON = "JSON"
        FILE = "FILE"

    @staticmethod
    def _get_pydantic_models(func: Callable) -> tuple[BaseModel, BaseModel]:
        signature = inspect.signature(func)
        field_name_to_field_type = {}
        for param_name, param in signature.parameters.items():
            if param.default != inspect.Parameter.empty:
                field_name_to_field_type[param_name] = (param.annotation, param.default)
            else:
                field_name_to_field_type[param_name] = (param.annotation, ...)
        argument_model = create_model(
            f"{func.__name__}_arg", **field_name_to_field_type
        )
        if signature.return_annotation != inspect.Parameter.empty and not issubclass(
            signature.return_annotation, Response
        ):
            result_model = create_model(
                f"{func.__name__}_result",
                result=(Optional[signature.return_annotation], None),
                error_message=(Optional[str], None),
            )
        else:
            result_model = create_model(
                f"{func.__name__}_result",
                result=(Any, None),
                error_message=(Optional[str], None),
            )
        return argument_model, result_model

    def __init__(
        self,
        on_invoke_strategy_command: Callable[[str], Coroutine],
        on_revoke_strategy_command: Callable[[str], Coroutine],
    ):
        self.base_config = get_base_config()
        self._strategy_name_to_strategy_map: Mapping[str, BaseStrategy] = {}
        self._on_invoke_strategy_command = on_invoke_strategy_command
        self._on_revoke_strategy_command = on_revoke_strategy_command

    def register_strategy(self, strategy_name: str, strategy: BaseStrategy):
        self._strategy_name_to_strategy_map[strategy_name] = strategy

    def serve(self, port: int):
        app = self._get_app()
        uvicorn.run(app=app, host="0.0.0.0", port=port)

    def _get_app(self) -> BaseFastAPI:
        app = BaseFastAPI(
            base_config=self.base_config,
            lifespan=self._api_server_lifespan,
            title="Strategy Manager",
            description=f"For strategies: {', '.join(self._strategy_name_to_strategy_map.keys())}",
        )
        strategy_router = APIRouter(prefix="/strategies")
        for strategy_name in self._strategy_name_to_strategy_map.keys():
            strategy_router.include_router(
                self._get_polymorphic_strategy_router(strategy_name=strategy_name)
            )
        strategy_router.include_router(self._get_generic_strategy_router())
        app.include_router(strategy_router)
        return app

    @asynccontextmanager
    async def _api_server_lifespan(self, app: BaseFastAPI):
        app.state.strategy_manager = self
        yield

    def _get_polymorphic_strategy_router(self, strategy_name: str) -> APIRouter:
        router = APIRouter(
            prefix=f"/{strategy_name}", tags=[f"Strategy<{strategy_name}>"]
        )
        strategy = self._strategy_name_to_strategy_map[strategy_name]

        for command_name in strategy.command_names:
            command = getattr(strategy, command_name)
            (
                _StrategyCommandArgumentSchema,
                _StrategyCommandResultSchema,
            ) = self._get_pydantic_models(command)

            def _closure(
                _StrategyCommandArgumentSchema,
                _StrategyCommandResultSchema,
                command_name,
            ):
                @router.post(
                    f"/{command_name}",
                    response_model=ResponseSchema[_StrategyCommandResultSchema],
                )
                async def _post_polymorphic_strategy_command_invoke(
                    strategy_command_argument: _StrategyCommandArgumentSchema,  # type: ignore
                    response_type: self.ResponseType = self.ResponseType.JSON,
                ):
                    command_result = _StrategyCommandResultSchema()
                    try:
                        result = await self._on_invoke_strategy_command(
                            strategy_name=strategy_name,
                            command_name=command_name,
                            command_args=(),
                            command_kwargs=strategy_command_argument.model_dump(),
                            should_wait_for_result=(
                                response_type != self.ResponseType.NO_WAIT
                            ),
                        )
                        if isinstance(result, Exception):
                            command_result.error_message = str(result)
                        elif isinstance(result, Response):
                            return result
                        else:
                            command_result.result = result
                    except StrategyManagerValidationError as e:
                        command_result.error_message = str(e)
                    return ResponseSchema[_StrategyCommandResultSchema](
                        status=StatusEnum.SUCCESS, data=command_result
                    )

            _closure(
                _StrategyCommandArgumentSchema,
                _StrategyCommandResultSchema,
                command_name,
            )
        CommandNameEnum = Enum(
            "CommandNameEnum",
            {v: v for v in strategy.command_names},
        )

        @router.post(
            "/{command_name}/revoke",
            response_model=ResponseSchema[StrategyCommandResultSchema],
        )
        async def _post_polymorphic_strategy_command_revoke(
            command_name: Annotated[CommandNameEnum, Path()],  # type: ignore
        ):
            command_result = StrategyCommandResultSchema()
            try:
                await self._on_revoke_strategy_command(
                    strategy_name=strategy_name, command_name=command_name.value
                )
            except StrategyManagerValidationError as e:
                command_result.error_message = str(e)
            return ResponseSchema[StrategyCommandResultSchema](
                status=StatusEnum.SUCCESS, data=command_result
            )

        return router

    def _get_generic_strategy_router(self) -> APIRouter:
        StrategyNameEnum = Enum(
            "StrategyNameEnum",
            {k: k for k in self._strategy_name_to_strategy_map.keys()},
        )
        router = APIRouter(prefix="", tags=["Strategy"])

        @router.post(
            "/{strategy_name}/commands/{command_name}/invoke",
            response_model=ResponseSchema[StrategyCommandResultSchema],
        )
        async def post_generic_strategy_command_invoke(
            strategy_name: Annotated[StrategyNameEnum, Path()],  # type: ignore
            command_name: Annotated[str, Path()],
            strategy_command_argument: StrategyCommandArgumentSchema,
            response_type: self.ResponseType = self.ResponseType.JSON,
        ):
            command_result = StrategyCommandResultSchema()
            try:
                result = await self._on_invoke_strategy_command(
                    strategy_name=strategy_name.value,
                    command_name=command_name,
                    command_args=strategy_command_argument.args,
                    command_kwargs=strategy_command_argument.kwargs,
                    should_wait_for_result=(response_type != self.ResponseType.NO_WAIT),
                )
                if isinstance(result, Exception):
                    command_result.error_message = str(result)
                elif isinstance(result, Response):
                    return result
                else:
                    command_result.result = result
            except StrategyManagerValidationError as e:
                command_result.error_message = str(e)
            return ResponseSchema[StrategyCommandResultSchema](
                status=StatusEnum.SUCCESS, data=command_result
            )

        @router.post(
            "/{strategy_name}/commands/{command_name}/revoke",
            response_model=ResponseSchema[StrategyCommandResultSchema],
        )
        async def post_generic_strategy_command_revoke(
            strategy_name: Annotated[StrategyNameEnum, Path()],  # type: ignore
            command_name: Annotated[str, Path()],
        ):
            command_result = StrategyCommandResultSchema()
            try:
                await self._on_revoke_strategy_command(
                    strategy_name=strategy_name.value, command_name=command_name
                )
            except StrategyManagerValidationError as e:
                command_result.error_message = str(e)
            return ResponseSchema[StrategyCommandResultSchema](
                status=StatusEnum.SUCCESS, data=command_result
            )

        return router
