"""
Hidden Gem Finder — surfaces off-the-beaten-path spots and local secrets.

Capability: "Uncover hidden gems"
Identifies lesser-known attractions, local-only spots, and authentic
experiences that typical tourists miss. Uses LLM to create vivid,
enticing descriptions that make the traveler want to visit.
"""

import logging

from data.loader import (
    filter_by_budget,
    filter_by_interests,
    filter_by_accessibility,
    filter_by_query,
)
from models.schemas import TravelRequest, HiddenGemResult
from tools.llm_helper import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a local insider who knows every hidden corner of Indian 
destinations. You help solo budget travelers discover spots that tourists miss.

Given a hidden gem and traveler context, write a vivid, sensory 2-3 sentence 
description that makes the traveler feel like they've already arrived. Include 
why most tourists miss this place and one insider tip.

Respond with ONLY the description — no headers, bullets, or formatting."""


async def find_hidden_gems(
    request: TravelRequest, destinations: list[dict]
) -> list[HiddenGemResult]:
    """Find hidden gems matching the user's interests and constraints.

    Collects hidden gems from filtered destinations, enriches descriptions
    with LLM for a personalized, vivid feel.

    Args:
        request: Validated travel request with interests and mobility needs.
        destinations: Pre-loaded destination dataset.

    Returns:
        List of HiddenGemResult with vivid descriptions.
    """
    filtered = filter_by_query(destinations, request.query)
    filtered = filter_by_budget(filtered, request.budget)
    filtered = filter_by_interests(filtered, request.interests)
    filtered = filter_by_accessibility(filtered, request.accessibility)

    if not filtered:
        filtered = filter_by_query(destinations, request.query) or destinations[:5]

    gems = []
    for dest in filtered:
        for gem in dest.get("hidden_gems", []):
            gems.append((dest, gem))

    # Limit to top 4 gems to avoid too many LLM calls
    gems = gems[:4]

    results = []
    for dest, gem in gems:
        user_context = (
            f"Traveler: {request.query}\n"
            f"Budget: {request.budget}\n"
            f"Interests: {', '.join(request.interests) if request.interests else 'general'}\n"
            f"Hidden Gem: {gem['name']} in {dest['name']}, {dest['region']}\n"
            f"Original description: {gem['description']}\n"
            f"Why hidden: {gem.get('why_hidden', 'Off the beaten path')}\n"
            f"Local tip: {gem.get('local_tip', '')}"
        )

        try:
            enriched_desc = await call_llm(SYSTEM_PROMPT, user_context)
        except (TimeoutError, RuntimeError) as exc:
            logger.warning("LLM enrichment failed for gem %s: %s", gem["name"], exc)
            enriched_desc = gem["description"]

        results.append(HiddenGemResult(
            name=gem["name"],
            location=f"{dest['name']}, {dest['region']}",
            description=enriched_desc,
            why_hidden=gem.get("why_hidden", ""),
            local_tip=gem.get("local_tip", ""),
        ))

    return results
