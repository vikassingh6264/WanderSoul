"""
Destination Recommender — recommends attractions matching user preferences.

Capability: "Recommend attractions"
Filters destinations by budget, available days, and interests,
then uses LLM to generate personalized recommendation blurbs
explaining why each destination fits the traveler's context.
"""

import logging

from data.loader import (
    filter_by_budget,
    filter_by_days,
    filter_by_interests,
    filter_by_accessibility,
    filter_by_query,
    score_destination,
)
from models.schemas import TravelRequest, DestinationResult
from tools.llm_helper import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a culturally sensitive travel advisor specializing in 
authentic, off-the-beaten-path Indian travel experiences. You help solo budget 
travelers find destinations that match their interests.

Given a destination and traveler context, write a SHORT (2-3 sentence) personalized 
recommendation explaining why this destination is perfect for THIS specific traveler.
Include one concrete budget tip.

Respond with ONLY the recommendation text — no headers, bullets, or formatting."""


async def recommend_destinations(
    request: TravelRequest, destinations: list[dict]
) -> list[DestinationResult]:
    """Recommend destinations matching the user's preferences.

    Filters by budget, days, interests, and accessibility, scores matches,
    then enriches top results with LLM-generated personalized blurbs.

    Args:
        request: Validated travel request with budget, days, interests.
        destinations: Pre-loaded destination dataset.

    Returns:
        List of DestinationResult with personalized recommendation text.
    """
    # Apply filters — query name match first to anchor results to requested destination
    filtered = filter_by_query(destinations, request.query)
    filtered = filter_by_budget(filtered, request.budget)
    filtered = filter_by_days(filtered, request.days)
    filtered = filter_by_interests(filtered, request.interests)
    filtered = filter_by_accessibility(filtered, request.accessibility)

    if not filtered:
        # Fallback: relax to query match + budget + days only
        filtered = filter_by_query(destinations, request.query)
        filtered = filter_by_budget(filtered, request.budget)
        filtered = filter_by_days(filtered, request.days)
        logger.info("Relaxed filters — using query+budget+days only, got %d results", len(filtered))

    # Score and rank
    scored = [
        (d, score_destination(d, request.budget, request.days, request.interests))
        for d in filtered
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_destinations = scored[:3]

    results = []
    for dest, score in top_destinations:
        user_context = (
            f"Traveler: {request.query}\n"
            f"Budget: {request.budget}, Days: {request.days}\n"
            f"Interests: {', '.join(request.interests) if request.interests else 'general exploration'}\n"
            f"Destination: {dest['name']} in {dest['region']}\n"
            f"Description: {dest['description']}\n"
            f"Highlights: {', '.join(dest.get('tags', []))}"
        )

        try:
            match_reason = await call_llm(SYSTEM_PROMPT, user_context)
        except (TimeoutError, RuntimeError) as exc:
            logger.warning("LLM enrichment failed for %s: %s", dest["name"], exc)
            match_reason = dest["description"]

        results.append(DestinationResult(
            name=dest["name"],
            region=dest["region"],
            match_reason=match_reason,
            budget_tip=f"Budget level: {dest.get('budget_level', 'medium')}",
            highlights=dest.get("tags", []),
        ))

    return results
