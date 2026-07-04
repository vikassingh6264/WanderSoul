"""
Unit tests for the web search tool and router fallback behaviour.

Key test: when the search API raises an exception (simulated via mock),
the agent must still return a valid TravelResponse from the curated JSON.
"""

import pytest
from unittest.mock import patch, MagicMock
from models.schemas import TravelRequest
from agent.router import _needs_live_search, _maybe_fetch_live_context_sync
from tools.web_search_tool import search_current_info, _cache


# ─── Fixtures ────────────────────────────────────────────────────

def _req(query: str, budget: str = "low", days: int = 3, interests=None) -> TravelRequest:
    return TravelRequest(
        query=query,
        budget=budget,
        days=days,
        interests=interests or [],
    )


SAMPLE_DESTINATIONS = [
    {
        "id": "jaipur",
        "name": "Jaipur",
        "region": "Rajasthan",
        "budget_level": "low",
        "best_for_days": [2, 3, 4],
        "tags": ["heritage", "street-food"],
        "accessibility": "good",
    }
]


# ─── _needs_live_search() decision logic ─────────────────────────

class TestNeedsLiveSearch:

    def test_time_keyword_triggers_search(self):
        req = _req("festivals in december in Rajasthan")
        should, reason = _needs_live_search(req, SAMPLE_DESTINATIONS)
        assert should is True
        assert "december" in reason

    def test_live_condition_keyword_triggers_search(self):
        req = _req("is Amber Fort open right now")
        should, reason = _needs_live_search(req, SAMPLE_DESTINATIONS)
        assert should is True
        assert "open" in reason

    def test_no_curated_match_triggers_search(self):
        # "scuba-diving" matches nothing in SAMPLE_DESTINATIONS
        req = _req("scuba diving spots", interests=["scuba-diving"])
        should, reason = _needs_live_search(req, SAMPLE_DESTINATIONS)
        assert should is True
        assert "no curated match" in reason

    def test_normal_query_does_not_trigger_search(self):
        req = _req("recommend hidden gems in Rajasthan", interests=["heritage"])
        should, reason = _needs_live_search(req, SAMPLE_DESTINATIONS)
        assert should is False
        assert reason == ""

    def test_generic_plan_query_does_not_trigger_search(self):
        req = _req("plan a 3 day budget trip")
        should, reason = _needs_live_search(req, SAMPLE_DESTINATIONS)
        assert should is False


# ─── search_current_info() graceful failure ───────────────────────

class TestSearchCurrentInfo:

    def setup_method(self):
        # Clear cache before each test
        _cache.clear()

    def test_returns_empty_list_when_api_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            # Ensure TAVILY_API_KEY is absent
            import os
            os.environ.pop("TAVILY_API_KEY", None)
            result = search_current_info("test query")
        assert result == []

    def test_returns_empty_list_on_network_exception(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("tools.web_search_tool.TavilyClient") as MockClient:
                MockClient.return_value.search.side_effect = Exception("network error")
                result = search_current_info("test query")
        assert result == []

    def test_returns_empty_list_on_timeout(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("tools.web_search_tool.TavilyClient") as MockClient:
                MockClient.return_value.search.side_effect = TimeoutError("timeout")
                result = search_current_info("test query")
        assert result == []

    def test_caches_successful_result(self):
        mock_response = {"results": [{"title": "T", "content": "S", "url": "http://x.com"}]}

        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("tools.web_search_tool.TavilyClient") as MockClient:
                MockClient.return_value.search.return_value = mock_response
                result1 = search_current_info("cached query")
                result2 = search_current_info("cached query")

        # SDK .search() should only be called once — second call hits cache
        assert MockClient.return_value.search.call_count == 1
        assert result1 == result2
        assert result1[0]["title"] == "T"


# ─── Fallback integration: search failure → curated JSON still works ─

class TestRouterFallbackOnSearchFailure:
    """
    Critical demo-safety test: even when the search API raises an exception,
    _maybe_fetch_live_context_sync must return [] and the router must
    continue to produce a valid response from the curated JSON.
    """

    def setup_method(self):
        _cache.clear()

    def test_search_exception_returns_empty_list(self):
        """Router sync helper returns [] when search raises — never propagates."""
        req = _req("festivals in december", interests=["heritage"])

        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("tools.web_search_tool.TavilyClient") as MockClient:
                MockClient.return_value.search.side_effect = RuntimeError("API down")
                result = _maybe_fetch_live_context_sync(req, SAMPLE_DESTINATIONS)

        assert result == [], "Search failure must return [], not raise"

    @pytest.mark.asyncio
    async def test_full_handle_request_survives_search_failure(self):
        """End-to-end: search API failure does not prevent a valid TravelResponse."""
        from agent.router import handle_request
        from data.loader import load_destinations

        load_destinations()  # ensure curated data is loaded

        req = _req(
            query="festivals in december in Rajasthan",
            budget="low",
            days=3,
            interests=["heritage"],
        )

        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("tools.web_search_tool.TavilyClient") as MockClient:
                MockClient.return_value.search.side_effect = RuntimeError("API down")
                with patch("tools.destination_recommender.recommend_destinations", return_value=[]):
                    with patch("tools.hidden_gem_finder.find_hidden_gems", return_value=[]):
                        with patch("tools.heritage_promoter.promote_heritage", return_value=[]):
                            with patch("tools.event_suggester.suggest_events", return_value=[]):
                                with patch("tools.experience_connector.connect_experiences", return_value=[]):
                                    with patch("tools.storytelling_generator.generate_story", return_value=None):
                                        response = await handle_request(req)

        # Must return a valid TravelResponse — not raise, not hang
        assert response is not None
        assert response.intent in ("events", "plan_trip", "discover", "explore", "story")
        assert isinstance(response.destinations, list)
        assert isinstance(response.summary, str)
