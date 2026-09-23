"""Built-in tool: safe mathematical expression calculator."""

from __future__ import annotations

import ast
import math
import operator

from pydantic import BaseModel, Field

from app.tools.registry import registry


class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate, e.g. '2 + 3 * 4'")


# Safe operators and functions
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node: ast.AST) -> float:
    """Recursively evaluate an AST node with only safe operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _SAFE_OPS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            args = [_safe_eval(a) for a in node.args]
            func = _SAFE_FUNCS[node.func.id]
            if callable(func):
                return func(*args)
            return func  # Constants like pi, e
        raise ValueError(f"Unsupported function: {ast.dump(node.func)}")
    elif isinstance(node, ast.Name) and node.id in _SAFE_FUNCS:
        val = _SAFE_FUNCS[node.id]
        if not callable(val):
            return val  # Constants
        raise ValueError(f"'{node.id}' requires arguments")
    else:
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")


@registry.register(
    name="calculator",
    description="Evaluate a mathematical expression safely. Supports +, -, *, /, **, %, sqrt, log, trig functions.",
    args_model=CalculatorInput,
)
def calculator(expression: str) -> str:
    """Safely evaluate a math expression without using eval()."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
        return f"{expression} = {result}"
    except (ValueError, TypeError, ZeroDivisionError) as e:
        return f"Error evaluating '{expression}': {e}"
