from __future__ import annotations

from typing import Any, Callable

from .context import Context
from .errors import UnknownToolError
from .tool import Tool


class Registry:
    def __init__(self, context: Context) -> None:
        self._context = context

    def tool(
        self,
        name: str,
        *,
        description: str,
        parameters: dict[str, Any] | None = None,
        block: Callable[..., Any] | None = None,
    ) -> Tool:
        new_tool = Tool(str(name), description, parameters or {}, block)
        self._context.register_tool(new_tool)
        return new_tool

    def dispatch(self, name: str, args: dict[str, Any] | None = None) -> Any:
        tool = self._context.tools.get(str(name))
        if tool is None:
            raise UnknownToolError(f"No tool registered as '{name}'")
        return tool.block(**(args or {}))
