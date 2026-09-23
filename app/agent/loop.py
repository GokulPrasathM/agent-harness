"""Core agent loop — the heart of the harness.

A clean, readable ~150-line async ReAct loop with production safeguards:
  - Bounded iterations
  - Cost budget circuit breaker
  - Timeout
  - Retry on transient errors
  - Tool error self-correction
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import litellm
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.agent.guardrail import check_scope
from app.agent.prompts import build_system_prompt
from app.agent.state import RunResult, RunStatus
from app.core.config import Settings, api_key_for_model
from app.core.cost import BudgetExceededError, CostTracker
from app.core.logging import get_logger
from app.tools.registry import ToolRegistry

log = get_logger("agent")


# --- Resilient LLM caller ---

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=1, max=15),
    retry=retry_if_exception_type(
        (litellm.exceptions.RateLimitError, litellm.exceptions.ServiceUnavailableError)
    ),
)
async def _call_llm(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    api_key: str | None = None,
) -> Any:
    """Call LLM with automatic retries on transient errors."""
    return await litellm.acompletion(
        model=model,
        api_key=api_key,
        messages=messages,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
    )


# --- Main agent loop ---

async def run_agent(
    user_message: str,
    settings: Settings,
    tool_registry: ToolRegistry,
) -> RunResult:
    """Run the agent loop for a single user message.

    This is the core function. It:
    1. Checks scope guardrail
    2. Runs bounded ReAct loop (think → tool → observe)
    3. Tracks cost and enforces budget
    4. Returns typed RunResult
    """
    config = settings.yaml_config
    start_time = time.time()
    api_key = api_key_for_model(config.agent.model, settings.secrets)

    log.info("agent_run_start", model=config.agent.model, user_message=user_message[:100])

    # --- Step 1: Scope guardrail ---
    scope_result = await check_scope(
        user_message=user_message,
        scope_config=config.scope,
        model=config.agent.model,
        api_key=api_key,
    )
    if not scope_result.in_scope:
        log.info("scope_rejected", reason=scope_result.reason)
        return RunResult(
            status=RunStatus.SCOPE_REJECTED,
            output=config.scope.rejection_message,
            duration_seconds=time.time() - start_time,
        )

    # --- Step 2: Build messages ---
    system_prompt = build_system_prompt(config)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # --- Step 3: Get tool schemas ---
    tool_schemas = tool_registry.get_schemas(enabled=config.tools.enabled)

    # --- Step 4: Agent loop ---
    cost_tracker = CostTracker(budget_usd=config.limits.max_cost_usd)

    async def _loop() -> RunResult:
        for iteration in range(config.limits.max_iterations):
            log.info("agent_turn", iteration=iteration + 1)

            # Call LLM
            try:
                response = await _call_llm(
                    model=config.agent.model,
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None,
                    api_key=api_key,
                )
            except Exception as e:
                log.error("llm_call_failed", error=str(e))
                # Try fallback model
                if config.agent.fallback_model != config.agent.model:
                    log.info("trying_fallback", model=config.agent.fallback_model)
                    fallback_api_key = api_key_for_model(
                        config.agent.fallback_model, settings.secrets
                    )
                    response = await _call_llm(
                        model=config.agent.fallback_model,
                        messages=messages,
                        tools=tool_schemas if tool_schemas else None,
                        api_key=fallback_api_key,
                    )
                else:
                    return RunResult(
                        status=RunStatus.ERROR,
                        output="Failed to get a response from the LLM.",
                        error=str(e),
                        iterations=iteration + 1,
                        total_cost_usd=cost_tracker.total_cost,
                        duration_seconds=time.time() - start_time,
                        messages=messages,
                    )

            # Track cost
            turn_cost = cost_tracker.track(response)
            log.info("turn_cost", cost=f"${turn_cost:.6f}", total=f"${cost_tracker.total_cost:.6f}")

            try:
                cost_tracker.check_budget()
            except BudgetExceededError as e:
                log.warning("budget_exceeded", detail=str(e))
                return RunResult(
                    status=RunStatus.BUDGET_EXCEEDED,
                    output=f"Agent stopped: {e}",
                    iterations=iteration + 1,
                    total_cost_usd=cost_tracker.total_cost,
                    duration_seconds=time.time() - start_time,
                    messages=messages,
                )

            # Extract response
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)

            # Append assistant message to history
            assistant_msg = {"role": "assistant", "content": message.content or ""}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_msg)

            # If no tool calls, we have the final answer
            if not tool_calls:
                log.info("agent_run_complete", iterations=iteration + 1)
                return RunResult(
                    status=RunStatus.SUCCESS,
                    output=message.content or "",
                    iterations=iteration + 1,
                    total_cost_usd=cost_tracker.total_cost,
                    duration_seconds=time.time() - start_time,
                    messages=messages,
                )

            # Execute tool calls
            for tc in tool_calls:
                log.info("tool_call", tool=tc.function.name)
                result = await tool_registry.execute(
                    name=tc.function.name,
                    args_json=tc.function.arguments,
                    max_output_chars=config.limits.max_tool_output_chars,
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        # Exhausted iterations
        log.warning("max_iterations_reached")
        return RunResult(
            status=RunStatus.MAX_ITERATIONS,
            output=messages[-1].get("content", "Agent reached maximum iterations."),
            iterations=config.limits.max_iterations,
            total_cost_usd=cost_tracker.total_cost,
            duration_seconds=time.time() - start_time,
            messages=messages,
        )

    # Run with timeout
    try:
        return await asyncio.wait_for(
            _loop(),
            timeout=config.limits.timeout_seconds,
        )
    except TimeoutError:
        log.warning("agent_timeout", timeout=config.limits.timeout_seconds)
        return RunResult(
            status=RunStatus.TIMEOUT,
            output=f"Agent timed out after {config.limits.timeout_seconds} seconds.",
            total_cost_usd=cost_tracker.total_cost,
            duration_seconds=time.time() - start_time,
            messages=messages,
        )
