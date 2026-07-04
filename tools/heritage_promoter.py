"""
Heritage Promoter — highlights cultural heritage and historical significance.

Capability: "Promote heritage"
Surfaces UNESCO sites, historical landmarks, traditional art forms,
and cultural practices that deserve preservation and recognition.
Uses LLM to explain why heritage matters and how travelers can
engage respectfully with historical and cultural sites.
"""

from models.schemas import TravelRequest, HeritageResult


async def promote_heritage(request: TravelRequest, destinations: list[dict]) -> list[HeritageResult]:
    """Highlight heritage sites and cultural significance for matching destinations.

    Args:
        request: Travel request providing context for relevance ranking.
        destinations: Pre-loaded destination dataset.

    Returns:
        List of HeritageResult with heritage narratives.
    """
    # TODO: Implement heritage filtering + LLM enrichment
    raise NotImplementedError
