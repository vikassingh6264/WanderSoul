"""
Experience Connector — connects travelers with authentic cultural experiences.

Capability: "Connect visitors with authentic cultural experiences"
Recommends hands-on cultural activities: cooking classes, artisan
workshops, homestays, guided walks with locals, temple ceremonies,
and community participation opportunities. Uses LLM to personalize
recommendations based on the traveler's comfort level and interests.
"""

import logging

from data.loader import filter_by_budget, filter_by_interests, filter_by_accessibility, filter_by_query
from models.schemas import TravelRequest, ExperienceResult
from tools.llm_helper import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a cultural experience curator who connects travelers with 
authentic, hands-on activities — cooking classes, artisan workshops, homestays, 
guided walks, and community events. You write for solo budget travelers who want 
to DO things, not just SEE things.

Given an experience and traveler context, write 2-3 sentences that:
1. Describe what the traveler will actually DO (not just see)
2. Explain the cultural significance of this activity
3. Include a practical detail (cost, how to book, what to expect)

Respond with ONLY the text — no headers, bullets, or formatting."""


async def connect_experiences(
    request: TravelRequest, destinations: list[dict]
) -> list[ExperienceResult]:
    """Connect the traveler with authentic cultural experiences.

    Collects hands-on experiences from filtered destinations, enriches
    with LLM for personalized activity descriptions.

    Args:
        request: Travel request with interests and comfort preferences.
        destinations: Pre-loaded destination dataset with experience info.

    Returns:
        List of ExperienceResult with personalized activity suggestions.
    """
    filtered = filter_by_query(destinations, request.query)
    filtered = filter_by_budget(filtered, request.budget)
    filtered = filter_by_interests(filtered, request.interests)
    filtered = filter_by_accessibility(filtered, request.accessibility)

    if not filtered:
        filtered = filter_by_query(destinations, request.query) or destinations[:5]

    experiences = []
    for dest in filtered:
        for exp in dest.get("cultural_experiences", []):
            experiences.append((dest, exp))

    # Limit to top 4 experiences
    experiences = experiences[:4]

    results = []
    for dest, exp in experiences:
        user_context = (
            f"Traveler: {request.query}\n"
            f"Budget: {request.budget}\n"
            f"Interests: {', '.join(request.interests) if request.interests else 'culture'}\n"
            f"Accessibility: {request.accessibility}\n"
            f"Experience: {exp['name']} in {dest['name']}, {dest['region']}\n"
            f"Type: {exp.get('type', 'cultural activity')}\n"
            f"Description: {exp['description']}\n"
            f"Budget estimate: {exp.get('budget_estimate', 'Affordable')}\n"
            f"Booking tip: {exp.get('booking_tip', 'Ask locally')}"
        )

        try:
            enriched = await call_llm(SYSTEM_PROMPT, user_context)
        except (TimeoutError, RuntimeError) as exc:
            logger.warning("Experience enrichment failed for %s: %s", exp["name"], exc)
            enriched = exp["description"]

        results.append(ExperienceResult(
            name=exp["name"],
            type=exp.get("type", "cultural"),
            description=enriched,
            budget_estimate=exp.get("budget_estimate", ""),
            booking_tip=exp.get("booking_tip", ""),
        ))

    return results
