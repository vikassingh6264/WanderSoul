"""
Storytelling Generator — creates immersive cultural narratives.

Capability: "Generate immersive storytelling"
Generates rich, sensory narratives about destinations that bring
the culture, history, and atmosphere to life. Weaves in local
legends, historical context, and sensory details (sights, sounds,
smells, tastes) to create an emotional connection before the
traveler even arrives.
"""

import logging

from models.schemas import TravelRequest, StoryResult
from tools.llm_helper import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a master storyteller who brings Indian destinations to life 
through vivid, sensory narratives. You write for solo budget travelers who want to 
feel the soul of a place, not just see its sights.

Write an immersive 4-5 paragraph narrative about the given destination. Include:
- A sensory opening (what the traveler sees, hears, smells as they arrive)
- Historical context woven naturally into the story (not as dry facts)
- A local legend or cultural tradition that reveals the destination's soul
- A moment of human connection (a conversation with a local, a shared meal)
- A closing that captures why this place stays with you

Write in second person ("you") to make it personal. Keep the total under 300 words.
Respond with ONLY the narrative — no title, no headers."""


async def generate_story(request: TravelRequest, destination: dict) -> StoryResult:
    """Generate an immersive cultural narrative for a destination.

    Uses the full destination data (description, heritage, experiences)
    as context for the LLM to craft a rich, personalized narrative.

    Args:
        request: Travel request providing persona context for tone/focus.
        destination: Single destination dict to build the story around.

    Returns:
        StoryResult with the narrative text and key themes.
    """
    user_context = (
        f"Traveler: {request.query}\n"
        f"Budget: {request.budget}, Days: {request.days}\n"
        f"Interests: {', '.join(request.interests) if request.interests else 'culture and exploration'}\n\n"
        f"Destination: {destination['name']}, {destination['region']}\n"
        f"Type: {destination.get('type', 'city')}\n"
        f"Description: {destination['description']}\n\n"
        f"Heritage: {_format_heritage(destination)}\n"
        f"Experiences: {_format_experiences(destination)}\n"
        f"Hidden gems: {_format_gems(destination)}"
    )

    try:
        narrative = await call_llm(SYSTEM_PROMPT, user_context)
    except (TimeoutError, RuntimeError) as exc:
        logger.warning("Story generation failed for %s: %s", destination["name"], exc)
        narrative = (
            f"Imagine arriving in {destination['name']}. "
            f"{destination['description']} "
            "Some stories are best discovered in person — this is one of them."
        )

    return StoryResult(
        destination=destination["name"],
        narrative=narrative,
        themes=destination.get("tags", [])[:4],
    )


def _format_heritage(destination: dict) -> str:
    """Format heritage sites into context string for the LLM.

    Args:
        destination: Destination dict with heritage_sites.

    Returns:
        Formatted string of heritage info.
    """
    sites = destination.get("heritage_sites", [])
    if not sites:
        return "Rich cultural heritage"
    return "; ".join(
        f"{s['name']}: {s['significance']}" for s in sites[:2]
    )


def _format_experiences(destination: dict) -> str:
    """Format cultural experiences into context string for the LLM.

    Args:
        destination: Destination dict with cultural_experiences.

    Returns:
        Formatted string of experience info.
    """
    exps = destination.get("cultural_experiences", [])
    if not exps:
        return "Authentic local experiences"
    return "; ".join(
        f"{e['name']}: {e['description'][:80]}" for e in exps[:2]
    )


def _format_gems(destination: dict) -> str:
    """Format hidden gems into context string for the LLM.

    Args:
        destination: Destination dict with hidden_gems.

    Returns:
        Formatted string of hidden gem info.
    """
    gems = destination.get("hidden_gems", [])
    if not gems:
        return "Off-the-beaten-path spots await"
    return "; ".join(
        f"{g['name']}: {g['description'][:80]}" for g in gems[:2]
    )
