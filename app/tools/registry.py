"""Tool registry — register tools with @tool decorator, auto-generate schemas."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from app.core.logging import get_logger

log = get_logger("tools")


class ToolRegistry:
    """Registry of tools available to the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
    ) -> Callable:
        """Decorator to register a tool function."""
        def decorator(func: Callable) -> Callable:
            self._tools[name] = func
            self._schemas[name] = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": args_model.model_json_schema(),
                },
            }
            return func
        return decorator

    def get_schemas(self, enabled: list[str] | None = None) -> list[dict[str, Any]]:
        """Get OpenAI-format tool schemas, optionally filtered by enabled list."""
        if enabled is None:
            return list(self._schemas.values())
        return [self._schemas[n] for n in enabled if n in self._schemas]

    async def execute(
        self, name: str, args_json: str, max_output_chars: int = 8000
    ) -> str:
        """Execute a tool by name. Returns result string or error string (never throws)."""
        if name not in self._tools:
            return f"Error: Tool '{name}' not found. Available: {list(self._tools.keys())}"
        try:
            kwargs = json.loads(args_json)
            func = self._tools[name]
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = await asyncio.to_thread(func, **kwargs)
            output = json.dumps(result) if not isinstance(result, str) else result
            # Truncate long outputs to prevent context overflow
            if len(output) > max_output_chars:
                output = output[:max_output_chars] + f"\n... [truncated, {len(output)} chars total]"
            return output
        except Exception as e:
            log.warning("tool_error", tool=name, error=str(e))
            return f"Error executing '{name}': {type(e).__name__}: {e}"

    def list_tools(self) -> list[dict[str, str]]:
        """List all registered tools with name and description."""
        return [
            {"name": s["function"]["name"], "description": s["function"]["description"]}
            for s in self._schemas.values()
        ]


# Global registry instance
registry = ToolRegistry()
