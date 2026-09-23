"""TEMPLATE: Copy this file to create a new tool.

Steps:
  1. Copy this file: cp _template.py my_tool.py
  2. Define your input model (Pydantic)
  3. Implement your function
  4. Register with @registry.register()
  5. Import in app/tools/__init__.py

That's it. The agent will auto-discover and use your tool.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.tools.registry import registry


# Step 1: Define your input schema
class MyToolInput(BaseModel):
    """Describe what arguments your tool takes."""

    query: str = Field(description="Describe this parameter for the LLM")
    # Add more fields as needed


# Step 2: Register and implement
@registry.register(
    name="my_tool",
    description="Describe what this tool does — the LLM reads this to decide when to use it.",
    args_model=MyToolInput,
)
async def my_tool(query: str) -> str:
    """Implement your tool logic here."""
    # Your code here
    result = f"Processed: {query}"
    return result
