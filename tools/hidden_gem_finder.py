"""
Hidden Gem Finder — surfaces off-the-beaten-path spots and local secrets.

Capability: "Uncover hidden gems"
Identifies lesser-known attractions, local-only spots, and authentic
experiences that typical tourists miss. Uses LLM to create vivid,
enticing descriptions that make the traveler want to visit.
"""

from models.schemas import TravelRequest, HiddenGemResult


async def find_hidden_gems(request: TravelRequest, destinations: list[dict]) -> list[HiddenGemResult]:
    """Find hidden gems matching the user's interests and constraints.

    Args:
        request: Validated travel request with interests and mobility needs.
        destinations: Pre-loaded destination dataset.

    Returns:
        List of HiddenGemResult with vivid descriptions.
    """
    # TODO: Implement hidden gem filtering + LLM enrichment
    raise NotImplementedError
