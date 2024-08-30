import asyncio
import inspect


class BaseStrategy:
    @property
    def command_names(self) -> list[str]:
        result = []
        for attribute_name in dir(self):
            if attribute_name.startswith("_"):
                continue
            if attribute_name == "command_names":
                continue
            attribute = getattr(self, attribute_name)
            is_async_function = asyncio.iscoroutinefunction(attribute)
            is_sync_function = inspect.ismethod(attribute)
            if not is_async_function and not is_sync_function:
                continue
            result.append(attribute_name)
        return result
