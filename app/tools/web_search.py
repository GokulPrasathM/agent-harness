"""Built-in tool: web search via Tavily API or fallback to DuckDuckGo."""

from __future__ import annotations

import os

import httpx
from pydantic import BaseModel, Field

from app.tools.registry import registry


class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up")
    max_results: int = Field(default=5, ge=1, le=10, description="Number of results to return")


async def _tavily_search(query: str, max_results: int) -> str:
    """Search using Tavily API (free tier: 1000 req/month)."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return await _duckduckgo_search(query, max_results)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": max_results},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.get('title', 'No title')}")
        lines.append(f"   URL: {r.get('url', '')}")
        lines.append(f"   {r.get('content', 'No snippet')[:300]}")
        lines.append("")
    return "\n".join(lines)


async def _duckduckgo_search(query: str, max_results: int) -> str:
    """Fallback: search using DuckDuckGo instant answer API (no key needed)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
        )
        resp.raise_for_status()
        data = resp.json()

    lines = [f"Search results for: {query}\n"]

    # Abstract
    abstract = data.get("AbstractText", "")
    if abstract:
        lines.append(f"Summary: {abstract[:500]}")
        lines.append(f"Source: {data.get('AbstractURL', '')}")
        lines.append("")

    # Related topics
    for i, topic in enumerate(data.get("RelatedTopics", [])[:max_results], 1):
        if isinstance(topic, dict) and "Text" in topic:
            lines.append(f"{i}. {topic['Text'][:300]}")
            lines.append(f"   URL: {topic.get('FirstURL', '')}")
            lines.append("")

    if len(lines) == 1:
        lines.append("No results found. Try a different query.")

    return "\n".join(lines)


@registry.register(
    name="web_search",
    description="Search the web for current information. Uses Tavily if API key is set, otherwise falls back to DuckDuckGo.",
    args_model=WebSearchInput,
)
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web and return formatted results."""
    return await _tavily_search(query, max_results)
