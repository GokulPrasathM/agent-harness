"""Built-in tool: fetch and extract text content from a URL."""

from __future__ import annotations

import re

import httpx
from pydantic import BaseModel, Field

from app.tools.registry import registry


class ReadUrlInput(BaseModel):
    url: str = Field(description="The URL to fetch and read content from")


def _strip_html(html: str) -> str:
    """Basic HTML to text conversion."""
    # Remove script and style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


@registry.register(
    name="read_url",
    description="Fetch a web page and extract its text content. Useful for reading articles, docs, or any public URL.",
    args_model=ReadUrlInput,
)
async def read_url(url: str) -> str:
    """Fetch a URL and return its text content."""
    headers = {"User-Agent": "AgentForge/1.0 (bot; +https://github.com/agent-forge)"}
    headers = {"User-Agent": "AgentHarness/1.0 (bot; +https://github.com/agent-harness)"}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "text/html" in content_type:
        text = _strip_html(resp.text)
    else:
        text = resp.text

    if not text.strip():
        return f"No readable content found at {url}"

    return f"Content from {url}:\n\n{text[:6000]}"
