"""
Optional live web search tool — wraps Tavily's search API via tavily-python SDK.

Equivalent to the JS pattern:
    const client = tavily({ apiKey: process.env.TAVILY_API_KEY });
    client.search(query, { searchDepth: "advanced" })

Design contract:
- Returns [] on ANY failure (timeout, missing key, API error) — never raises.
- In-memory cache keyed by query string, TTL = 30 minutes.
- Only called when the router explicitly decides live data is needed.
- TAVILY_API_KEY is read from .env; if absent, search is silently skipped.
"""

import logging
import time
import os

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None  # SDK not installed — search will be skipped gracefully

logger = logging.getLogger(__name__)

# ── Cache ────────────────────────────────────────────────────────
_cache: dict[str, tuple[list, float]] = {}  # query → (results, timestamp)
_CACHE_TTL = 1800  # 30 minutes


def _get_cached(query: str) -> list | None:
    entry = _cache.get(query)
    if entry and (time.time() - entry[1]) < _CACHE_TTL:
        return entry[0]
    return None


def _set_cache(query: str, results: list) -> None:
    _cache[query] = (results, time.time())


# ── Public API ───────────────────────────────────────────────────

def search_current_info(query: str, max_results: int = 3) -> list[dict]:
    """Search for current/live information using the Tavily SDK.

    Mirrors the JS @tavily/core pattern with searchDepth='advanced'.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default 3).

    Returns:
        List of {title, snippet, url} dicts, or [] on any failure.
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        logger.info("TAVILY_API_KEY not set — skipping web search")
        return []

    cached = _get_cached(query)
    if cached is not None:
        logger.info("Web search cache hit for: %s", query)
        return cached

    try:
        if TavilyClient is None:
            logger.warning("tavily-python not installed — skipping web search")
            return []

        client = TavilyClient(api_key=api_key)
        # search_depth="advanced" matches the JS snippet: { searchDepth: "advanced" }
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
        )
        raw = response.get("results", [])
        results = [
            {
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "url": r.get("url", ""),
            }
            for r in raw[:max_results]
        ]
        _set_cache(query, results)
        logger.info("Web search returned %d results for: %s", len(results), query)
        return results

    except Exception as exc:
        logger.warning("Web search failed (returning []): %s", exc)
        return []
