"""
Integration tests for FastAPI API endpoints.

Tests input validation, error handling, and response schemas
using FastAPI's TestClient (no real LLM calls needed for validation tests).
"""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


# ─── Health Check Tests ─────────────────────────────────────────

class TestHealthCheck:
    """Tests for the /api/health endpoint."""

    def test_health_returns_200(self):
        """Health check should return 200 with status healthy."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "WanderSoul"


# ─── Destinations List Tests ────────────────────────────────────

class TestDestinationsList:
    """Tests for the /api/destinations endpoint."""

    def test_destinations_returns_list(self):
        """Should return a list of destinations with count."""
        response = client.get("/api/destinations")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "destinations" in data
        assert data["count"] > 0

    def test_destination_has_required_fields(self):
        """Each destination should have id, name, region, tags."""
        response = client.get("/api/destinations")
        data = response.json()
        dest = data["destinations"][0]
        assert "id" in dest
        assert "name" in dest
        assert "region" in dest
        assert "tags" in dest


# ─── Input Validation Tests ─────────────────────────────────────

class TestInputValidation:
    """Tests for input validation on the /api/discover endpoint."""

    def test_empty_query_returns_422(self):
        """Empty or too-short query should be rejected with 422."""
        response = client.post("/api/discover", json={
            "query": "",
            "budget": "low",
            "days": 3,
        })
        assert response.status_code == 422

    def test_short_query_returns_422(self):
        """Query shorter than 3 characters should be rejected."""
        response = client.post("/api/discover", json={
            "query": "hi",
            "budget": "low",
            "days": 3,
        })
        assert response.status_code == 422

    def test_whitespace_query_returns_422(self):
        """Whitespace-only input should be rejected instead of slipping through."""
        response = client.post("/api/discover", json={
            "query": "   ",
            "budget": "low",
            "days": 3,
        })
        assert response.status_code == 422

    def test_invalid_days_returns_422(self):
        """Days outside 1-30 range should be rejected."""
        response = client.post("/api/discover", json={
            "query": "recommend destinations",
            "budget": "low",
            "days": 0,
        })
        assert response.status_code == 422

    def test_missing_budget_returns_422(self):
        """Missing required budget field should be rejected."""
        response = client.post("/api/discover", json={
            "query": "recommend destinations",
            "days": 3,
        })
        assert response.status_code == 422

    def test_missing_body_returns_422(self):
        """Request with no body should be rejected."""
        response = client.post("/api/discover")
        assert response.status_code == 422
