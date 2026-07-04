"""
Event Suggester — recommends local events, festivals, and gatherings.

Capability: "Suggest local events"
Matches travelers with local festivals, cultural events, markets,
and community gatherings based on their travel dates, interests,
and location. Uses LLM to contextualize events for the specific
traveler's background and interests.
"""

import logging

from data.loader import filter_by_budget, filter_by_interests, filter_by_query
from models.schemas import TravelRequest, EventResult
from tools.llm_helper import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a local events insider who connects travelers with 
festivals, markets, and cultural gatherings they'd otherwise miss. You write 
for solo budget travelers who want authentic experiences.

Given a local event and traveler context, write 2-3 sentences that:
1. Paint a vivid picture of what the traveler will experience at this event
2. Explain why this event is especially relevant to their interests
3. Include one practical tip (timing, what to bring, what to expect)

Respond with ONLY the text — no headers, bullets, or formatting."""


async def suggest_events(
    request: TravelRequest, destinations: list[dict]
) -> list[EventResult]:
    """Suggest local events and festivals matching the user's travel context.

    Collects events from filtered destinations, enriches descriptions
    with LLM for personalized relevance and practical tips.

    Args:
        request: Travel request with dates, interests, and location.
        destinations: Pre-loaded destination dataset with event info.

    Returns:
        List of EventResult with contextualized event descriptions.
    """
    filtered = filter_by_query(destinations, request.query)
    filtered = filter_by_budget(filtered, request.budget)
    filtered = filter_by_interests(filtered, request.interests)

    if not filtered:
        filtered = filter_by_query(destinations, request.query) or destinations[:5]

    events = []
    for dest in filtered:
        for event in dest.get("local_events", []):
            events.append((dest, event))

    # Limit to top 4 events
    events = events[:4]

    results = []
    for dest, event in events:
        user_context = (
            f"Traveler: {request.query}\n"
            f"Budget: {request.budget}, Days: {request.days}\n"
            f"Interests: {', '.join(request.interests) if request.interests else 'culture'}\n"
            f"Event: {event['name']} in {dest['name']}, {dest['region']}\n"
            f"Timing: {event['timing']}\n"
            f"Description: {event['description']}\n"
            f"Relevance: {event.get('traveler_relevance', 'A must-see cultural experience')}"
        )

        try:
            enriched = await call_llm(SYSTEM_PROMPT, user_context)
        except (TimeoutError, RuntimeError) as exc:
            logger.warning("Event enrichment failed for %s: %s", event["name"], exc)
            enriched = event["description"]

        results.append(EventResult(
            name=event["name"],
            location=f"{dest['name']}, {dest['region']}",
            timing=event["timing"],
            description=enriched,
            traveler_relevance=event.get("traveler_relevance", ""),
        ))

    return results
