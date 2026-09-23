"""Per-run cost tracking with budget circuit breaker."""

from __future__ import annotations

from dataclasses import dataclass, field

import litellm


class BudgetExceededError(Exception):
    """Raised when the cost budget for a run is exceeded."""


@dataclass
class CostTracker:
    """Tracks token usage and cost across an agent run."""

    budget_usd: float = 0.50
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    turns: int = 0
    cost_per_turn: list[float] = field(default_factory=list)

    def track(self, response) -> float:
        """Track cost from a LiteLLM completion response. Returns turn cost."""
        try:
            turn_cost = litellm.completion_cost(completion_response=response)
        except Exception:
            turn_cost = 0.0

        usage = getattr(response, "usage", None)
        if usage:
            self.total_input_tokens += getattr(usage, "prompt_tokens", 0)
            self.total_output_tokens += getattr(usage, "completion_tokens", 0)

        self.total_cost += turn_cost
        self.turns += 1
        self.cost_per_turn.append(turn_cost)
        return turn_cost

    def check_budget(self) -> None:
        """Raise BudgetExceededError if budget is exceeded."""
        if self.total_cost > self.budget_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.total_cost:.4f} spent, "
                f"limit is ${self.budget_usd:.4f}"
            )

    def summary(self) -> dict:
        """Return a cost summary dict."""
        return {
            "total_cost_usd": round(self.total_cost, 6),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "turns": self.turns,
        }
