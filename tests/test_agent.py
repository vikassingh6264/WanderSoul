"""
Unit tests for the agent decision/routing logic.

Tests that different user contexts route to different strategies,
and that edge cases are handled correctly. These tests verify the
decision logic WITHOUT making real LLM calls.
"""

import pytest
from models.schemas import TravelRequest
from agent.router import classify_intent, select_strategy, _build_summary


# ─── Test Fixtures ───────────────────────────────────────────────

def _make_request(
    query: str = "recommend destinations",
    budget: str = "low",
    days: int = 3,
    interests: list[str] | None = None,
    accessibility: str = "none",
) -> TravelRequest:
    """Helper to create a TravelRequest with sensible defaults."""
    return TravelRequest(
        query=query,
        budget=budget,
        days=days,
        interests=interests or [],
        accessibility=accessibility,
    )


# ─── Intent Classification Tests ────────────────────────────────

class TestClassifyIntent:
    """Tests for classify_intent() — the first stage of the routing pipeline."""

    def test_discover_intent_from_recommendation_query(self):
        """Queries about finding/recommending places should route to 'discover'."""
        request = _make_request(query="Recommend me some destinations in Rajasthan")
        intent = classify_intent(request)
        assert intent == "discover"

    def test_explore_intent_from_hidden_gems_query(self):
        """Queries about hidden/secret/offbeat spots should route to 'explore'."""
        request = _make_request(query="Show me hidden gems and secret local spots")
        intent = classify_intent(request)
        assert intent == "explore"

    def test_events_intent_from_festival_query(self):
        """Queries about festivals/events should route to 'events'."""
        request = _make_request(query="What festivals and events are happening?")
        intent = classify_intent(request)
        assert intent == "events"

    def test_story_intent_from_narrative_query(self):
        """Queries asking for stories/narratives should route to 'story'."""
        request = _make_request(query="Tell me about the history and culture of Varanasi")
        intent = classify_intent(request)
        assert intent == "story"

    def test_plan_trip_intent_from_comprehensive_query(self):
        """Queries about full trip planning should route to 'plan_trip'."""
        request = _make_request(query="Help me plan a complete 3 days budget trip")
        intent = classify_intent(request)
        assert intent == "plan_trip"

    def test_ambiguous_query_defaults_to_plan_trip(self):
        """Queries with no matching keywords should default to 'plan_trip'."""
        request = _make_request(query="I love India and want something amazing")
        intent = classify_intent(request)
        assert intent == "plan_trip"


# ─── Strategy Selection Tests ───────────────────────────────────

class TestSelectStrategy:
    """Tests for select_strategy() — the persona-driven routing logic."""

    def test_discover_strategy_includes_destinations_and_heritage(self):
        """Discover intent should always include destinations + heritage."""
        request = _make_request(query="recommend places")
        strategy = select_strategy("discover", request)
        assert "destinations" in strategy["tools"]
        assert "heritage" in strategy["tools"]

    def test_discover_adds_experiences_when_interests_present(self):
        """Discover with specific interests should also return experiences."""
        request = _make_request(
            query="recommend places",
            interests=["street-food", "crafts"],
        )
        strategy = select_strategy("discover", request)
        assert "experiences" in strategy["tools"]

    def test_explore_includes_story_for_multiday_trips(self):
        """Explore intent should include storytelling for 2+ day trips."""
        request = _make_request(query="hidden gems", days=3)
        strategy = select_strategy("explore", request)
        assert strategy["include_story"] is True

    def test_explore_excludes_story_for_single_day(self):
        """Explore intent should skip storytelling for 1-day trips (not enough time)."""
        request = _make_request(query="hidden gems", days=1)
        strategy = select_strategy("explore", request)
        assert strategy["include_story"] is False

    def test_events_adds_hidden_gems_for_budget_travelers(self):
        """Budget travelers looking at events should also get hidden gems."""
        request = _make_request(query="festivals", budget="low")
        strategy = select_strategy("events", request)
        assert "events" in strategy["tools"]
        assert "hidden_gems" in strategy["tools"]

    def test_plan_trip_invokes_all_tools(self):
        """Full trip planning should invoke all tool categories."""
        request = _make_request(query="plan trip", days=3)
        strategy = select_strategy("plan_trip", request)
        expected_tools = {"destinations", "hidden_gems", "heritage", "events", "experiences"}
        assert expected_tools == set(strategy["tools"])
        assert strategy["include_story"] is True


# ─── Summary Builder Tests ──────────────────────────────────────

class TestBuildSummary:
    """Tests for the response summary builder."""

    def test_summary_includes_result_counts(self):
        """Summary should mention the count of each result type found."""
        results = {
            "destinations": [1, 2],
            "hidden_gems": [1],
            "events": [],
        }
        request = _make_request(days=3, budget="low")
        summary = _build_summary("discover", results, request)
        assert "2 destinations" in summary
        assert "1 hidden gem" in summary

    def test_empty_results_returns_fallback_message(self):
        """Empty results should return a helpful fallback message."""
        results = {}
        request = _make_request(days=1, budget="low")
        summary = _build_summary("discover", results, request)
        assert "adjusting" in summary.lower() or "finding" in summary.lower()
