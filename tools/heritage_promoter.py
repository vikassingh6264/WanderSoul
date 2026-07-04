"""
Heritage Promoter — highlights cultural heritage and historical significance.

Capability: "Promote heritage"
Surfaces UNESCO sites, historical landmarks, traditional art forms,
and cultural practices that deserve preservation and recognition.
Uses LLM to explain why heritage matters and how travelers can
engage respectfully with historical and cultural sites.
"""

import logging

from data.loader import filter_by_budget, filter_by_interests, filter_by_query
from models.schemas import TravelRequest, HeritageResult
from tools.llm_helper import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a cultural heritage advocate who helps travelers understand 
WHY heritage matters and HOW they can engage respectfully. You write for solo budget 
travelers who are genuinely curious about history and culture.

Given a heritage site and traveler context, write 2-3 sentences that:
1. Explain the site's significance in a way that creates emotional connection
2. Give one specific way the traveler can engage meaningfully (not just photograph)
3. Mention its preservation status if relevant

Respond with ONLY the text — no headers, bullets, or formatting."""


async def promote_heritage(
    request: TravelRequest, destinations: list[dict]
) -> list[HeritageResult]:
    """Highlight heritage sites and cultural significance for matching destinations.

    Collects heritage sites from filtered destinations and enriches them
    with LLM-generated narratives about significance and engagement.

    Args:
        request: Travel request providing context for relevance ranking.
        destinations: Pre-loaded destination dataset.

    Returns:
        List of HeritageResult with heritage narratives.
    """
    filtered = filter_by_query(destinations, request.query)
    filtered = filter_by_budget(filtered, request.budget)
    filtered = filter_by_interests(filtered, request.interests)

    if not filtered:
        filtered = filter_by_query(destinations, request.query) or destinations[:5]

    sites = []
    for dest in filtered:
        for site in dest.get("heritage_sites", []):
            sites.append((dest, site))

    # Limit to top 3 to control LLM calls
    sites = sites[:3]

    results = []
    for dest, site in sites:
        user_context = (
            f"Traveler: {request.query}\n"
            f"Budget: {request.budget}\n"
            f"Interests: {', '.join(request.interests) if request.interests else 'culture'}\n"
            f"Heritage Site: {site['name']} in {dest['name']}, {dest['region']}\n"
            f"Significance: {site['significance']}\n"
            f"How to engage: {site.get('how_to_engage', 'Visit respectfully')}\n"
            f"Preservation: {site.get('preservation_note', 'Maintained by local authorities')}"
        )

        try:
            enriched = await call_llm(SYSTEM_PROMPT, user_context)
        except (TimeoutError, RuntimeError) as exc:
            logger.warning("Heritage enrichment failed for %s: %s", site["name"], exc)
            enriched = site["significance"]

        results.append(HeritageResult(
            name=site["name"],
            significance=enriched,
            how_to_engage=site.get("how_to_engage", "Visit respectfully and learn the history."),
            preservation_note=site.get("preservation_note", ""),
        ))

    return results
