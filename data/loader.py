"""
Data loader — loads the curated destination dataset once at startup.

Reads destinations.json into memory so we never re-read from disk
on every request. Provides filtering helpers used by all tool functions.
"""

import json
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)

# Module-level cache — loaded once, reused across all requests
_destinations: list[dict] = []


def load_destinations() -> list[dict]:
    """Load destinations from JSON file into memory.

    Called once at app startup. Subsequent calls return the cached list.

    Returns:
        List of destination dicts.

    Raises:
        FileNotFoundError: If the destinations file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    global _destinations

    if _destinations:
        return _destinations

    data_path = Path(config.DESTINATIONS_FILE)
    if not data_path.exists():
        raise FileNotFoundError(f"Destinations file not found: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if isinstance(raw_data, dict) and "destinations" in raw_data:
        items = raw_data["destinations"]
    else:
        items = raw_data

    # Normalize fields to support varying schemas (like new state/region, budget abbreviation)
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        d = item.copy()
        
        # Normalize state/region — handle both missing key and explicit null value
        if not d.get("region"):
            d["region"] = d.get("state") or "India"
            
        # Normalize budget_level
        budget = str(d.get("budget_level", "medium")).lower()
        if budget.startswith("med"):
            d["budget_level"] = "medium"
        elif budget.startswith("low"):
            d["budget_level"] = "low"
        elif budget.startswith("high"):
            d["budget_level"] = "high"
        else:
            d["budget_level"] = "medium"
            
        # Normalize best_for_days (if missing, allow range [1..30] so days filter passes)
        if "best_for_days" not in d:
            d["best_for_days"] = list(range(1, 31))
            
        # Normalize accessibility
        if "accessibility" not in d:
            d["accessibility"] = "moderate"
            
        normalized.append(d)

    _destinations = normalized
    logger.info("Loaded %d destinations from %s", len(_destinations), data_path.name)
    return _destinations


def get_destinations() -> list[dict]:
    """Get the cached destination list (must call load_destinations first).

    Returns:
        List of destination dicts.
    """
    if not _destinations:
        return load_destinations()
    return _destinations


def filter_by_budget(destinations: list[dict], budget: str) -> list[dict]:
    """Filter destinations that match or are below the given budget level.

    Budget levels: low < medium < high.

    Args:
        destinations: List of destination dicts to filter.
        budget: User's budget level string.

    Returns:
        Filtered list of destinations.
    """
    budget_order = {"low": 1, "medium": 2, "high": 3}
    user_budget = budget_order.get(budget.lower(), 2)
    return [
        d for d in destinations
        if budget_order.get(d.get("budget_level", "medium"), 2) <= user_budget
    ]


def filter_by_days(destinations: list[dict], days: int) -> list[dict]:
    """Filter destinations suitable for the given number of days.

    Args:
        destinations: List of destination dicts to filter.
        days: Number of available days.

    Returns:
        Destinations where the user's days fall within best_for_days range.
    """
    return [
        d for d in destinations
        if days >= min(d.get("best_for_days", [1]))
        and days <= max(d.get("best_for_days", [30]))
    ]


def filter_by_interests(destinations: list[dict], interests: list[str]) -> list[dict]:
    """Filter destinations matching at least one user interest.

    Args:
        destinations: List of destination dicts to filter.
        interests: List of interest tag strings.

    Returns:
        Destinations with at least one matching tag.
    """
    if not interests:
        return destinations

    interest_set = {i.lower() for i in interests}
    return [
        d for d in destinations
        if interest_set & {t.lower() for t in d.get("tags", [])}
    ]


def filter_by_accessibility(destinations: list[dict], accessibility: str) -> list[dict]:
    """Filter destinations based on accessibility needs.

    Args:
        destinations: List of destination dicts to filter.
        accessibility: User's accessibility requirement.

    Returns:
        Filtered destinations. If 'none', returns all.
    """
    if not accessibility or accessibility.lower() == "none":
        return destinations

    accessible_levels = {"good", "moderate"}
    return [
        d for d in destinations
        if d.get("accessibility", "moderate").lower() in accessible_levels
    ]


def score_destination(destination: dict, budget: str, days: int, interests: list[str]) -> float:
    """Score a destination's relevance to the user's context.

    Higher score = better match. Used for ranking results.

    Args:
        destination: Single destination dict.
        budget: User's budget level.
        days: Available days.
        interests: User's interest tags.

    Returns:
        Float score between 0.0 and 1.0.
    """
    score = 0.0

    # Budget match (0.3 weight)
    budget_order = {"low": 1, "medium": 2, "high": 3}
    user_budget = budget_order.get(budget.lower(), 2)
    dest_budget = budget_order.get(destination.get("budget_level", "medium"), 2)
    if dest_budget <= user_budget:
        score += 0.3
    if dest_budget == user_budget:
        score += 0.1  # Exact match bonus

    # Days fit (0.3 weight)
    best_days = destination.get("best_for_days", [1, 2, 3])
    if days in best_days:
        score += 0.3
    elif min(best_days) <= days <= max(best_days):
        score += 0.15

    # Interest overlap (0.3 weight)
    if interests:
        dest_tags = {t.lower() for t in destination.get("tags", [])}
        interest_set = {i.lower() for i in interests}
        overlap = len(dest_tags & interest_set)
        if overlap > 0:
            score += min(0.3, 0.1 * overlap)

    return round(min(score, 1.0), 2)
