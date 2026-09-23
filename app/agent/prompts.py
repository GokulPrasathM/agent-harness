"""System prompt builder — loads instructions from config and injects dynamic context."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import AgentYamlConfig


def build_system_prompt(config: AgentYamlConfig) -> str:
    """Build the system prompt from config + dynamic context."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    parts = [
        config.instructions.strip(),
        "",
        f"Current date/time: {now}",
    ]

    if config.scope.enabled:
        parts.extend([
            "",
            "IMPORTANT: You must ONLY respond to queries within your defined scope.",
            f"Your scope: {config.scope.description}",
            "If a query is outside your scope, politely decline.",
        ])

    return "\n".join(parts)
