"""Scope guardrail — checks if user input is within the agent's defined scope."""

from __future__ import annotations

import json

import litellm
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.agent.state import ScopeResult
from app.core.config import ScopeConfig
from app.core.logging import get_logger

log = get_logger("guardrail")

_SCOPE_CHECK_PROMPT = """You are a scope classifier. Determine if the user's message falls within the allowed scope.

Allowed scope: {scope_description}

User message: {user_message}

Respond with ONLY a JSON object:
{{"in_scope": true/false, "reason": "brief explanation"}}"""


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential_jitter(initial=1, max=5),
    retry=retry_if_exception_type((litellm.exceptions.RateLimitError,)),
)
async def check_scope(
    user_message: str,
    scope_config: ScopeConfig,
    model: str = "openai/gpt-4o-mini",
    api_key: str | None = None,
) -> ScopeResult:
    """Check if a user message is within the agent's defined scope.

    Uses a fast, cheap LLM call to classify. Returns ScopeResult.
    """
    if not scope_config.enabled:
        return ScopeResult(in_scope=True, reason="Scope check disabled")

    prompt = _SCOPE_CHECK_PROMPT.format(
        scope_description=scope_config.description,
        user_message=user_message,
    )

    try:
        response = await litellm.acompletion(
            model=model,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
        )
        content = response.choices[0].message.content.strip()

        # Parse JSON response
        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        data = json.loads(content)
        result = ScopeResult(
            in_scope=data.get("in_scope", True),
            reason=data.get("reason", ""),
        )
        log.info("scope_check", in_scope=result.in_scope, reason=result.reason)
        return result

    except Exception as e:
        # On error, default to allowing (fail-open) so the agent isn't blocked
        log.warning("scope_check_error", error=str(e))
        return ScopeResult(in_scope=True, reason=f"Scope check failed: {e}")
