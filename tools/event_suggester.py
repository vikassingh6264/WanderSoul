"""
Event Suggester — recommends local events, festivals, and gatherings.

Capability: "Suggest local events"
Matches travelers with local festivals, cultural events, markets,
and community gatherings based on their travel dates, interests,
and location. Uses LLM to contextualize events for the specific
traveler's background and interests.
"""

from models.schemas import TravelRequest, EventResult


async def suggest_events(request: TravelRequest, destinations: list[dict]) -> list[EventResult]:
    """Suggest local events and festivals matching the user's travel context.

    Args:
        request: Travel request with dates, interests, and location.
        destinations: Pre-loaded destination dataset with event info.

    Returns:
        List of EventResult with contextualized event descriptions.
    """
    # TODO: Implement event matching + LLM enrichment
    raise NotImplementedError
