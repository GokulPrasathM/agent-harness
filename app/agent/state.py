"""Typed state models for agent runs."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    SUCCESS = "success"
    MAX_ITERATIONS = "max_iterations_reached"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"
    SCOPE_REJECTED = "scope_rejected"
    ERROR = "error"


class RunResult(BaseModel):
    """Result of an agent run."""

    status: RunStatus
    output: str
    iterations: int = 0
    total_cost_usd: float = 0.0
    duration_seconds: float = 0.0
    error: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)


class ScopeResult(BaseModel):
    """Result of a scope guardrail check."""

    in_scope: bool
    reason: str = ""
