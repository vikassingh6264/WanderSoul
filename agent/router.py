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

from data.loader import get_destinations, filter_by_budget, filter_by_days, score_destination, filter_by_interests
from models.schemas import TravelRequest, TravelResponse
from tools.destination_recommender import recommend_destinations
from tools.hidden_gem_finder import find_hidden_gems
from tools.storytelling_generator import generate_story
from tools.heritage_promoter import promote_heritage
from tools.event_suggester import suggest_events
from tools.experience_connector import connect_experiences
from tools.web_search_tool import search_current_info

logger = logging.getLogger(__name__)

# ── Live-search trigger keywords ─────────────────────────────────
# Condition (a): user mentions a specific time/season
_TIME_KEYWORDS = [
    "this weekend", "this week", "today", "tonight", "tomorrow",
    "in january", "in february", "in march", "in april", "in may",
    "in june", "in july", "in august", "in september", "in october",
    "in november", "in december", "this month", "next month",
    "monsoon", "winter", "summer", "spring", "autumn",
]
# Condition (b): user asks about current/live conditions
_LIVE_CONDITION_KEYWORDS = [
    "is open", "are open", "currently", "right now", "current price",
    "current weather", "weather", "open now", "still open",
    "how much does it cost", "entry fee", "ticket price",
]


def _needs_live_search(request: TravelRequest, destinations_data: list[dict]) -> tuple[bool, str]:
    """Decide whether live web search is warranted for this request.

    Returns (True, reason) only for one of three explicit conditions:
      a) A specific date/season is mentioned → check live events.
      b) User asks about current conditions (weather, prices, open/closed).
      c) The curated JSON has NO matching destination for the requested
         interest+region combination.

    For everything else returns (False, "") — curated JSON is used alone.

    Args:
        request: Validated travel request.
        destinations_data: Already-loaded curated destination list.

    Returns:
        (should_search: bool, reason: str)
    """
    q = request.query.lower()

    # Condition (a) — time/season reference
    for kw in _TIME_KEYWORDS:
        if kw in q:
            return True, f"time reference detected ('{kw}') — checking live events"

    # Condition (b) — live condition query
    for kw in _LIVE_CONDITION_KEYWORDS:
        if kw in q:
            return True, f"live-condition query detected ('{kw}') — fetching current info"

    # Condition (c) — curated JSON has no match for interests + region
    if request.interests:
        matched = filter_by_interests(
            filter_by_budget(destinations_data, request.budget),
            request.interests,
        )
        if not matched:
            return True, (
                f"no curated match for interests {request.interests} "
                f"at budget '{request.budget}' — searching live"
            )

    return False, ""


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

    # Decide whether live search is needed — runs before tool tasks
    live_results = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _maybe_fetch_live_context_sync(request, destinations_data)
    )

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
    summary = _build_summary(strategy["intent"], results, request, live_results)

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


def _maybe_fetch_live_context_sync(request: TravelRequest, destinations_data: list[dict]) -> list[dict]:
    """Synchronous wrapper for _maybe_fetch_live_context, used with run_in_executor."""
    should_search, reason = _needs_live_search(request, destinations_data)
    if not should_search:
        print("[WanderSoul] Using curated dataset (no live search needed)")
        logger.info("Live search skipped — using curated dataset")
        return []
    search_query = f"{request.query} India travel"
    print(f"[WanderSoul] Fetching live update for: {search_query} | Reason: {reason}")
    logger.info("Live search triggered — %s", reason)
    return search_current_info(search_query)


def _build_summary(intent: str, results: dict, request: TravelRequest, live_results: list[dict] | None = None) -> str:
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

    base = (
        f"Found {', '.join(parts)} matching your "
        f"{request.days}-day {request.budget}-budget trip. "
        "Each recommendation is tailored to your interests!"
    ) if parts else "We're finding the best cultural experiences for you. Try adjusting your preferences for more results."

    if live_results:
        snippets = " | ".join(
            f"Recent update: {r['title']} — {r['snippet'][:120]}"
            for r in live_results[:2]
            if r.get("title") and r.get("snippet")
        )
        if snippets:
            base = f"{base}\n\n{snippets}"

    return base


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
