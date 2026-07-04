"""
Unit tests for the data loader and filtering functions.

Tests data loading, budget filtering, days filtering, interest
matching, and destination scoring — the foundation all tools rely on.
"""

import pytest
from data.loader import (
    filter_by_budget,
    filter_by_days,
    filter_by_interests,
    filter_by_accessibility,
    score_destination,
)


# ─── Test Data ───────────────────────────────────────────────────

SAMPLE_DESTINATIONS = [
    {
        "id": "test_low",
        "name": "Budget City",
        "region": "TestRegion",
        "budget_level": "low",
        "best_for_days": [1, 2, 3],
        "tags": ["heritage", "street-food"],
        "accessibility": "good",
    },
    {
        "id": "test_medium",
        "name": "Mid City",
        "region": "TestRegion",
        "budget_level": "medium",
        "best_for_days": [3, 4, 5],
        "tags": ["adventure", "trekking"],
        "accessibility": "limited",
    },
    {
        "id": "test_high",
        "name": "Luxury City",
        "region": "TestRegion",
        "budget_level": "high",
        "best_for_days": [5, 7, 10],
        "tags": ["luxury", "spa"],
        "accessibility": "good",
    },
]


# ─── Budget Filtering Tests ─────────────────────────────────────

class TestBudgetFiltering:
    """Tests for filter_by_budget() — ensures budget constraints are respected."""

    def test_low_budget_only_returns_low_destinations(self):
        """Low budget should only match low-budget destinations."""
        result = filter_by_budget(SAMPLE_DESTINATIONS, "low")
        assert len(result) == 1
        assert result[0]["name"] == "Budget City"

    def test_medium_budget_returns_low_and_medium(self):
        """Medium budget should match both low and medium destinations."""
        result = filter_by_budget(SAMPLE_DESTINATIONS, "medium")
        assert len(result) == 2
        names = {d["name"] for d in result}
        assert names == {"Budget City", "Mid City"}

    def test_high_budget_returns_all(self):
        """High budget should match all destinations."""
        result = filter_by_budget(SAMPLE_DESTINATIONS, "high")
        assert len(result) == 3


# ─── Days Filtering Tests ───────────────────────────────────────

class TestDaysFiltering:
    """Tests for filter_by_days() — ensures day-count constraints work."""

    def test_three_days_matches_appropriate_destinations(self):
        """3 days should match destinations where 3 is in best_for_days."""
        result = filter_by_days(SAMPLE_DESTINATIONS, 3)
        names = {d["name"] for d in result}
        assert "Budget City" in names
        assert "Mid City" in names
        assert "Luxury City" not in names

    def test_one_day_only_matches_short_trip_destinations(self):
        """1 day should only match destinations suitable for day trips."""
        result = filter_by_days(SAMPLE_DESTINATIONS, 1)
        assert len(result) == 1
        assert result[0]["name"] == "Budget City"


# ─── Interest Filtering Tests ───────────────────────────────────

class TestInterestFiltering:
    """Tests for filter_by_interests() — ensures interest matching works."""

    def test_matching_interests_returns_correct_destinations(self):
        """Interests matching destination tags should return those destinations."""
        result = filter_by_interests(SAMPLE_DESTINATIONS, ["heritage"])
        assert len(result) == 1
        assert result[0]["name"] == "Budget City"

    def test_empty_interests_returns_all(self):
        """Empty interest list should return all destinations (no filtering)."""
        result = filter_by_interests(SAMPLE_DESTINATIONS, [])
        assert len(result) == 3

    def test_no_matching_interests_returns_empty(self):
        """Interests that match no tags should return empty list."""
        result = filter_by_interests(SAMPLE_DESTINATIONS, ["underwater-basket-weaving"])
        assert len(result) == 0


# ─── Accessibility Filtering Tests ──────────────────────────────

class TestAccessibilityFiltering:
    """Tests for filter_by_accessibility()."""

    def test_none_accessibility_returns_all(self):
        """No accessibility requirement should return all destinations."""
        result = filter_by_accessibility(SAMPLE_DESTINATIONS, "none")
        assert len(result) == 3

    def test_accessibility_filter_excludes_limited(self):
        """Accessibility filtering should exclude 'limited' destinations."""
        result = filter_by_accessibility(SAMPLE_DESTINATIONS, "wheelchair-friendly")
        names = {d["name"] for d in result}
        assert "Mid City" not in names  # "limited" accessibility


# ─── Scoring Tests ──────────────────────────────────────────────

class TestScoring:
    """Tests for score_destination() — ensures scoring logic is correct."""

    def test_perfect_match_scores_highest(self):
        """A destination matching budget, days, and interests should score high."""
        dest = SAMPLE_DESTINATIONS[0]  # low budget, 1-3 days, heritage + street-food
        score = score_destination(dest, "low", 2, ["heritage", "street-food"])
        assert score >= 0.7

    def test_no_match_scores_low(self):
        """A destination matching nothing should score low."""
        dest = SAMPLE_DESTINATIONS[2]  # high budget, 5-10 days, luxury
        score = score_destination(dest, "low", 1, ["heritage"])
        assert score <= 0.3

    def test_score_between_zero_and_one(self):
        """All scores should be between 0 and 1."""
        for dest in SAMPLE_DESTINATIONS:
            score = score_destination(dest, "medium", 3, ["heritage"])
            assert 0.0 <= score <= 1.0
