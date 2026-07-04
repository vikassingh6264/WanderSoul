"""
Destination Recommender — recommends attractions matching user preferences.

Capability: "Recommend attractions"
Filters destinations by budget, available days, and interests,
then uses LLM to generate personalized recommendation blurbs
explaining why each destination fits the traveler's context.
"""

from models.schemas import TravelRequest, DestinationResult


async def recommend_destinations(request: TravelRequest, destinations: list[dict]) -> list[DestinationResult]:
    """Recommend destinations matching the user's preferences.

    Args:
        request: Validated travel request with budget, days, interests.
        destinations: Pre-loaded destination dataset.

    Returns:
        List of DestinationResult with personalized recommendation text.
    """
    # TODO: Implement filtering + LLM enrichment
    raise NotImplementedError
