from __future__ import annotations

from typing import Any

import requests
from langchain_core.tools import tool

from settings import env_int, env_str


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _extract_organic_results(payload: dict[str, Any], max_results: int) -> tuple[str, list[str]]:
    snippets: list[str] = []
    sources: list[str] = []

    for index, result in enumerate(payload.get("organic_results", [])[:max_results], start=1):
        title = result.get("title") or "Untitled result"
        link = result.get("link") or ""
        snippet = result.get("snippet") or result.get("description") or ""

        if link:
            sources.append(link)
        if snippet:
            snippets.append(f"[SERP source {index}: {title}]\nURL: {link}\n{snippet}")

    answer_box = payload.get("answer_box") or {}
    answer = answer_box.get("answer") or answer_box.get("snippet")
    answer_link = answer_box.get("link")
    if answer:
        snippets.insert(0, f"[SERP answer box]\nURL: {answer_link or ''}\n{answer}")
        if answer_link:
            sources.append(answer_link)

    return "\n\n".join(snippets), sorted(set(sources))


def search_web(query: str, max_results: int | None = None) -> tuple[str, list[str]]:
    api_key = env_str("SERPAPI_API_KEY", "")
    if not api_key:
        return "SERP API search failed: SERPAPI_API_KEY is missing.", []

    result_count = max_results or env_int("WEB_SEARCH_MAX_RESULTS", 5)
    params = {
        "engine": env_str("SERPAPI_ENGINE", "google"),
        "q": query,
        "api_key": api_key,
        "num": result_count,
    }

    location = env_str("SERPAPI_LOCATION", "")
    if location:
        params["location"] = location

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=env_int("SERPAPI_TIMEOUT", 20))
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return f"SERP API search failed: {exc}", []
    except ValueError:
        return "SERP API search failed: invalid JSON response.", []

    if payload.get("error"):
        return f"SERP API search failed: {payload['error']}", []

    return _extract_organic_results(payload, result_count)


@tool
def serpapi_search_tool(query: str) -> str:
    """Search the web with SerpAPI for non-Debales or current external information."""
    context, _sources = search_web(query)
    return context
