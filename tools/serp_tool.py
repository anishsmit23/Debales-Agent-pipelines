from __future__ import annotations

import warnings

from langchain_core.tools import tool

from settings import env_int

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover
    warnings.filterwarnings(
        "ignore",
        message=r"This package \(`duckduckgo_search`\) has been renamed to `ddgs`!.*",
        category=RuntimeWarning,
    )
    from duckduckgo_search import DDGS


def search_web(query: str, max_results: int | None = None) -> tuple[str, list[str]]:
    result_count = max_results or env_int("WEB_SEARCH_MAX_RESULTS", 5)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=result_count))
    except Exception as exc:
        return f"Web search failed: {exc}", []

    snippets: list[str] = []
    sources: list[str] = []
    for index, result in enumerate(results, start=1):
        title = result.get("title", "Untitled result")
        href = result.get("href", "")
        body = result.get("body", "")
        if href:
            sources.append(href)
        if body:
            snippets.append(f"[Web source {index}: {title}]\nURL: {href}\n{body}")

    return "\n\n".join(snippets), sources


@tool
def duckduckgo_search_tool(query: str) -> str:
    """Search the web for current or non-Debales information."""
    context, _sources = search_web(query)
    return context
