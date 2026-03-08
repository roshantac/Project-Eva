"""Tool decorator and registry: register async functions as BaseTool-compatible tools."""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from .models import BaseTool, ToolDef, ToolResult

F = TypeVar("F", bound=Callable[..., Any])

# Default JSON Schema for no-arg tools
EMPTY_PARAMS: dict[str, Any] = {"type": "object", "properties": {}, "required": []}


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
) -> Callable[[F], "RegisteredTool"]:
    """
    Decorator to register an async function as a tool.

    The function must have signature async def fn(params: dict[str, Any]) -> ToolResult
    or async def fn(**kwargs) with kwargs matching the JSON Schema properties.

    Args:
        name: Tool name (used by the LLM; lowercase, letters, numbers, underscores).
        description: What the tool does and when to use it.
        parameters: JSON Schema for parameters (type, properties, required). Default: {}.
    """

    def decorator(fn: F) -> RegisteredTool:
        params_schema = parameters if parameters is not None else EMPTY_PARAMS
        t = RegisteredTool(name=name, description=description, parameters=params_schema, fn=fn)
        register_tool(t)
        return t

    return decorator


_registry: list["RegisteredTool"] = []


def register_tool(t: "RegisteredTool") -> None:
    """Add a tool to the registry."""
    if t not in _registry:
        _registry.append(t)


def get_registered_tools() -> list["RegisteredTool"]:
    """Return all registered tools."""
    return list(_registry)


def clear_registry() -> None:
    """Clear the registry (mainly for tests)."""
    _registry.clear()


class RegisteredTool(BaseTool):
    """Wraps a registered async function as a BaseTool-compatible object."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        fn: Callable[..., Any],
    ) -> None:
        self._name = name
        self._description = description
        self._parameters = parameters
        self._fn = fn

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    def to_def(self) -> ToolDef:
        return ToolDef(name=self._name, description=self._description, parameters=self._parameters)

    def to_tool_schema(self) -> dict[str, Any]:
        return self.to_def().to_tool_schema()

    def to_ollama_tool(self) -> dict[str, Any]:
        return self.to_tool_schema()

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        result = await self._fn(params)
        if isinstance(result, ToolResult):
            return result
        if isinstance(result, str):
            return ToolResult(success=True, content=result)
        return ToolResult(success=True, content=str(result))
