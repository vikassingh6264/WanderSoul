"""
Agent router — the explicit decision/routing logic for WanderSoul.

This module contains the core decision-making function that inspects
user context (budget, days, interests, mobility/accessibility needs)
and routes to the appropriate tool functions. The routing logic is:

1. Rule-based intent classification (keyword + context analysis)
2. Strategy selection based on persona constraints
3. Tool orchestration — calling the right tools in the right order

Flow:
    User Input → classify_intent() → select_strategy() → execute_strategy()
                                                              ↓
                                                    Tool calls (parallel
                                                    where possible)
                                                              ↓
                                                    Formatted response

This decision logic is readable, testable, and NOT hidden inside
a single giant prompt string.
"""

import asyncio
import logging

from data.loader import get_destinations, filter_by_budget, filter_by_days, score_destination
from models.schemas import TravelRequest, TravelResponse
from tools.destination_recommender import recommend_destinations
from tools.hidden_gem_finder import find_hidden_gems
from tools.storytelling_generator import generate_story
from tools.heritage_promoter import promote_heritage
from tools.event_suggester import suggest_events
from tools.experience_connector import connect_experiences

logger = logging.getLogger(__name__)

# Intent keywords — used for rule-based classification
INTENT_KEYWORDS = {
    "discover": [
        "recommend", "suggest", "find", "where", "destination", "place",
        "visit", "travel", "go", "trip", "explore city", "see",
    ],
    "explore": [
        "hidden", "secret", "offbeat", "off-beat", "local", "authentic",
        "untouristy", "non-touristy", "gem", "unique", "unusual",
    ],
    "story": [
        "story", "tell me about", "history", "narrative", "culture of",
        "what is", "describe", "imagine", "feel", "experience of",
    ],
    "events": [
        "event", "festival", "fair", "celebration", "happening",
        "what's on", "when", "ceremony", "market", "gathering",
    ],
    "plan_trip": [
        "plan", "itinerary", "full trip", "complete", "everything",
        "all", "comprehensive", "guide", "help me plan", "3 days",
        "weekend", "budget trip",
    ],
}


def classify_intent(request: TravelRequest) -> str:
    """Classify the user's primary intent from their query and context.

    Uses keyword matching against the query text. Falls back to
    'plan_trip' for ambiguous queries (the most comprehensive response).

    Args:
        request: Validated travel request with user context.

    Returns:
        One of: 'discover', 'explore', 'plan_trip', 'events', 'story'.
    """
    query_lower = request.query.lower()

    scores: dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        scores[intent] = score

    best_intent = max(scores, key=scores.get)

    # If no keywords matched (all scores = 0), default to plan_trip
    if scores[best_intent] == 0:
        logger.info("No intent keywords matched, defaulting to plan_trip")
        return "plan_trip"

    logger.info("Classified intent as '%s' (score: %d)", best_intent, scores[best_intent])
    return best_intent


def select_strategy(intent: str, request: TravelRequest) -> dict:
    """Select which tools to invoke based on intent and persona context.

    Applies persona-driven rules:
    - Budget filtering determines which destinations are considered
    - Day count affects whether storytelling is included (needs >= 2 days)
    - Accessibility needs filter out inaccessible destinations
    - Interests drive which tool results are prioritized

    Args:
        intent: Classified intent string.
        request: Validated travel request.

    Returns:
        Strategy dict with 'tools' list and 'include_story' flag.
    """
    strategy = {
        "tools": [],
        "include_story": False,
        "intent": intent,
    }

    if intent == "discover":
        strategy["tools"] = ["destinations", "heritage"]
        # Add experiences if user has specific interests
        if request.interests:
            strategy["tools"].append("experiences")

    elif intent == "explore":
        strategy["tools"] = ["hidden_gems", "experiences"]
        # Add storytelling for multi-day trips
        if request.days >= 2:
            strategy["include_story"] = True

    elif intent == "story":
        strategy["include_story"] = True
        strategy["tools"] = ["destinations"]

    elif intent == "events":
        strategy["tools"] = ["events"]
        # Budget travelers also want hidden gems
        if request.budget.lower() in ("low", "budget"):
            strategy["tools"].append("hidden_gems")

    elif intent == "plan_trip":
        # Comprehensive — invoke everything
        strategy["tools"] = [
            "destinations", "hidden_gems", "heritage",
            "events", "experiences",
        ]
        if request.days >= 2:
            strategy["include_story"] = True

    else:
        # Fallback: full plan
        strategy["tools"] = ["destinations", "hidden_gems", "events"]
        strategy["include_story"] = request.days >= 2

    logger.info(
        "Strategy selected: tools=%s, include_story=%s",
        strategy["tools"], strategy["include_story"],
    )
    return strategy


async def execute_strategy(strategy: dict, request: TravelRequest) -> TravelResponse:
    """Execute the selected strategy by invoking the appropriate tools.

    Runs independent tools concurrently with asyncio.gather for speed.
    Handles individual tool failures gracefully — one failing tool
    doesn't break the entire response.

    Args:
        strategy: Strategy dict from select_strategy().
        request: Original travel request for context.

    Returns:
        Assembled TravelResponse with results from all invoked tools.
    """
    destinations_data = get_destinations()

    # Build async tasks for concurrent execution
    tasks = {}
    tool_list = strategy["tools"]

    if "destinations" in tool_list:
        tasks["destinations"] = recommend_destinations(request, destinations_data)

    if "hidden_gems" in tool_list:
        tasks["hidden_gems"] = find_hidden_gems(request, destinations_data)

    if "heritage" in tool_list:
        tasks["heritage"] = promote_heritage(request, destinations_data)

    if "events" in tool_list:
        tasks["events"] = suggest_events(request, destinations_data)

    if "experiences" in tool_list:
        tasks["experiences"] = connect_experiences(request, destinations_data)

    # Execute all tools concurrently
    results = {}
    if tasks:
        task_keys = list(tasks.keys())
        task_coroutines = list(tasks.values())

        gathered = await asyncio.gather(*task_coroutines, return_exceptions=True)

        for key, result in zip(task_keys, gathered):
            if isinstance(result, Exception):
                logger.error("Tool '%s' failed: %s", key, str(result))
                results[key] = []
            else:
                results[key] = result

    # Generate story if needed (depends on destination results)
    story = None
    if strategy["include_story"]:
        # Pick the top destination for the story
        story_dest = _pick_story_destination(destinations_data, request)
        if story_dest:
            try:
                story = await generate_story(request, story_dest)
            except Exception as exc:
                logger.error("Storytelling failed: %s", str(exc))

    # Build summary
    summary = _build_summary(strategy["intent"], results, request)

    return TravelResponse(
        intent=strategy["intent"],
        destinations=results.get("destinations", []),
        hidden_gems=results.get("hidden_gems", []),
        story=story,
        heritage=results.get("heritage", []),
        events=results.get("events", []),
        experiences=results.get("experiences", []),
        summary=summary,
    )


def _pick_story_destination(destinations_data: list[dict], request: TravelRequest) -> dict | None:
    """Pick the best destination for storytelling based on user context.

    Args:
        destinations_data: Full destination dataset.
        request: User's travel request.

    Returns:
        Best matching destination dict, or None.
    """
    filtered = filter_by_budget(destinations_data, request.budget)
    filtered = filter_by_days(filtered, request.days)

    if not filtered:
        filtered = destinations_data[:3]

    scored = [
        (d, score_destination(d, request.budget, request.days, request.interests))
        for d in filtered
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0] if scored else None


def _build_summary(intent: str, results: dict, request: TravelRequest) -> str:
    """Build a human-readable summary of the response.

    Args:
        intent: Classified user intent.
        results: Dict of tool name → result list.
        request: Original travel request.

    Returns:
        Summary string.
    """
    parts = []

    dest_count = len(results.get("destinations", []))
    gem_count = len(results.get("hidden_gems", []))
    event_count = len(results.get("events", []))
    heritage_count = len(results.get("heritage", []))
    exp_count = len(results.get("experiences", []))

    if dest_count:
        parts.append(f"{dest_count} destination{'s' if dest_count != 1 else ''}")
    if gem_count:
        parts.append(f"{gem_count} hidden gem{'s' if gem_count != 1 else ''}")
    if heritage_count:
        parts.append(f"{heritage_count} heritage site{'s' if heritage_count != 1 else ''}")
    if event_count:
        parts.append(f"{event_count} local event{'s' if event_count != 1 else ''}")
    if exp_count:
        parts.append(f"{exp_count} cultural experience{'s' if exp_count != 1 else ''}")

    if parts:
        return (
            f"Found {', '.join(parts)} matching your "
            f"{request.days}-day {request.budget}-budget trip. "
            "Each recommendation is tailored to your interests!"
        )
    return "We're finding the best cultural experiences for you. Try adjusting your preferences for more results."


async def handle_request(request: TravelRequest) -> TravelResponse:
    """Top-level entry point: classify → select → execute.

    This is the single function called by the FastAPI endpoint.

    Args:
        request: Validated travel request.

    Returns:
        Complete travel response.
    """
    intent = classify_intent(request)
    strategy = select_strategy(intent, request)
    response = await execute_strategy(strategy, request)
    return response
