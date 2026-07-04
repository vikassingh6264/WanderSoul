# WanderSoul — Discover Culture, Not Crowds

> AI-powered destination discovery for solo budget travelers who want authentic cultural experiences over tourist traps.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LLM](https://img.shields.io/badge/LLM-Groq%20(Llama%203.3)-purple)
![Tests](https://img.shields.io/badge/Tests-35%20passing-brightgreen)

---

## 1. Chosen Vertical & Persona

**Vertical:** Destination Discovery & Cultural Experiences

**Persona:** Solo backpacker, 3 days in the city, ₹5,000 budget, wants offbeat local culture and food over touristy Instagram spots, prefers walkable/low-mobility-friendly options.

This persona drives every design decision:
- **Budget filtering** eliminates luxury-only destinations upfront
- **Day-count constraints** ensure recommendations fit the traveler's window
- **Interest matching** prioritizes street food, heritage, crafts, and local experiences
- **Accessibility** filters out destinations marked as "limited" when needed
- **Hidden gems** are surfaced over mainstream attractions in explore mode

---

## 2. Approach & Logic

### Decision Flow

```
┌──────────────────────────────────┐
│         User Submits Query       │
│  (budget, days, interests, etc.) │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│       classify_intent()          │
│  Keyword-based intent detection  │
│  → discover | explore | story    │
│    events | plan_trip            │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│       select_strategy()          │
│  Persona-driven tool selection:  │
│  • Budget → filter destinations  │
│  • Days < 2 → skip storytelling  │
│  • Low budget + events → add gems│
│  • Has interests → add experiences│
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│       execute_strategy()         │
│  Concurrent tool invocation:     │
│  asyncio.gather() for speed      │
│  Each tool: filter → LLM enrich  │
│  Graceful degradation on failure │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│        TravelResponse            │
│  destinations + gems + heritage  │
│  + events + experiences + story  │
└──────────────────────────────────┘
```

### Why This Maps to Real Traveler Needs

1. **Budget-first filtering** — a backpacker on ₹5,000/day shouldn't see luxury resorts
2. **Day-count awareness** — no point recommending a 7-day valley trek to someone with 2 days
3. **Interest-driven routing** — "hidden gems" queries get different tools than "plan my trip"
4. **Graceful degradation** — if one LLM call fails, the rest still return results
5. **Storytelling for longer trips** — only generated when the traveler has time to immerse

---

## 3. Architecture Overview

```
project/
├── agent/
│   └── router.py         # classify_intent → select_strategy → execute_strategy
├── tools/
│   ├── llm_helper.py     # Shared LLM client (Groq) with timeout + cache
│   ├── destination_recommender.py   # Capability 1: Recommend attractions
│   ├── hidden_gem_finder.py         # Capability 2: Uncover hidden gems
│   ├── storytelling_generator.py    # Capability 3: Immersive storytelling
│   ├── heritage_promoter.py         # Capability 4: Promote heritage
│   ├── event_suggester.py           # Capability 5: Suggest local events
│   └── experience_connector.py      # Capability 6: Authentic experiences
├── data/
│   ├── loader.py          # Load-once + filtering + scoring
│   └── destinations.json  # 15 curated Indian destinations
├── models/
│   └── schemas.py         # Pydantic request/response schemas
├── tests/
│   ├── test_agent.py      # 14 tests: intent classification + strategy selection
│   ├── test_tools.py      # 13 tests: data filtering + scoring
│   └── test_api.py        # 8 tests: endpoints + input validation
├── frontend/
│   ├── index.html         # Semantic HTML with full ARIA support
│   ├── style.css          # Dark mode, glassmorphism, responsive
│   └── app.js             # Form handling, tabs, loading states
├── main.py                # FastAPI app with rate limiting
├── config.py              # Centralized settings from .env
├── requirements.txt       # Pinned dependencies
└── .env.example           # Placeholder config values
```

**Key architectural decisions:**
- **6 separate tool modules** — one per required GenAI capability, each independently testable
- **Agent router is pure logic** — intent classification and strategy selection are plain Python functions, not hidden inside a prompt
- **Data loaded once at startup** — no file I/O on every request
- **LLM responses cached** — identical prompts return cached results
- **Concurrent tool execution** — `asyncio.gather()` runs independent tools in parallel

---

## 4. Live Data (optional)

The app works **fully without a search API key**. The curated JSON dataset (`data/destinations.json`) is always the primary data source and is always available — no network dependency, no rate limits, zero latency.

Adding a `TAVILY_API_KEY` to your `.env` unlocks a second, optional capability: the agent can fetch live information for queries that genuinely need it.

### When live search is triggered (and when it isn't)

The router calls the search API **only** when one of these three conditions is true:

| Condition | Example query |
|---|---|
| A specific date or season is mentioned | *"festivals in December in Rajasthan"* |
| User asks about current conditions | *"is Amber Fort open right now"*, *"current entry fee"* |
| Curated JSON has no match for the requested interest+budget combination | interests that don't exist in the dataset |

For every other query the router prints `[WanderSoul] Using curated dataset (no live search needed)` and skips the API call entirely.

### Graceful degradation

If the search API is unavailable, rate-limited, or times out (6 s hard limit), `search_current_info()` returns an empty list and the agent continues normally using the curated JSON. The user never sees an error. This is verified by a dedicated unit test (`tests/test_web_search.py::TestRouterFallbackOnSearchFailure`).

### Setup

```bash
# In your .env file — both keys are optional
TAVILY_API_KEY=your-tavily-api-key-here   # get free key at https://app.tavily.com
```

When live results are included in a response, they are prefixed with `Recent update:` in the summary so the user can clearly distinguish freshly fetched data from curated facts.

---

## 5. How to Run Locally

### Prerequisites
- Python 3.10+
- A free Groq API key ([get one here](https://console.groq.com/keys))

### Setup

```bash
# Clone the repo
git clone https://github.com/vikassingh6264/WanderSoul.git
cd WanderSoul

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the server
uvicorn main:app --reload

# Open in browser
# → http://localhost:8000
```

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## 6. How the Solution Works — Example User Journey

**Scenario:** A solo traveler types: *"I want to explore hidden temples and street food in Rajasthan on a tight budget for 3 days"*

1. **Form Submission** → Frontend validates input, sends POST to `/api/discover`

2. **Input Validation** → Pydantic validates: query ≥ 3 chars, days 1-30, budget is set

3. **Intent Classification** (`classify_intent()`)
   - Keywords "hidden" + "explore" match → intent = `explore`

4. **Strategy Selection** (`select_strategy()`)
   - Intent `explore` → tools: `hidden_gems`, `experiences`
   - Days = 3 (≥ 2) → `include_story = True`

5. **Data Filtering** (in each tool)
   - Budget "low" → filters to 12/15 destinations
   - Interests ["heritage", "street-food"] → Jaipur, Varanasi, Jodhpur, Pushkar match
   - Days 3 → further narrows to those suitable for 3-day visits

6. **LLM Enrichment** (via Groq, concurrent calls)
   - Hidden gem finder generates vivid descriptions for Panna Meena ka Kund, Kabir Chaura, etc.
   - Storytelling generator crafts a sensory narrative about Jaipur
   - Experience connector suggests block printing workshops, chai conversations

7. **Response Assembly** → Results returned as structured JSON

8. **Frontend Rendering**
   - Tabbed interface shows: Hidden Gems, Experiences, Story
   - Cards with descriptions, local tips, budget estimates
   - Story tab shows immersive 2nd-person narrative

---

## 7. Assumptions Made

- **India focus** — the curated dataset covers 15 Indian destinations. A production version would expand globally.
- **Static dataset** — destinations and events are in a JSON file, not a live database. Events have seasonal timing info but no real-time calendar integration.
- **Free-tier LLM** — uses Groq's free tier (Llama 3.3 70B). Response quality and speed depend on Groq's availability.
- **Single user** — rate limiting is in-memory; a production version would use Redis or similar.
- **No authentication** — the API is open. A production version would add user accounts and saved trips.

---

## 8. Security Notes

- **No secrets in code** — API keys loaded from `.env` via `python-dotenv`. `.env` is in `.gitignore`.
- **`.env.example`** committed with placeholder values only — no real keys.
- **Input validation** — all endpoints use Pydantic models with field constraints (`min_length`, `ge/le` bounds).
- **No stack traces leaked** — global exception handler logs errors server-side, returns generic messages to clients.
- **No `eval()` or `exec()`** — no dynamic code execution anywhere.
- **No shell commands** — no `subprocess` calls, no file path injection surface.
- **XSS prevention** — frontend escapes all API response data before rendering in DOM.
- **Rate limiting** — in-memory token bucket prevents abuse (10 requests/60s per IP).

---

## 9. Known Limitations / What I'd Add With More Time

| Limitation | What I'd Add |
|---|---|
| Static JSON dataset | PostgreSQL + admin panel for destination management |
| In-memory rate limiting | Redis-backed rate limiting for multi-instance deployment |
| No user accounts | Auth (OAuth/JWT) + saved trips + trip history |
| No real-time events | Integration with local event APIs + calendar-aware suggestions |
| English only | Multi-language support (Hindi, regional languages) |
| No images | Destination photos via Unsplash API or curated image set |
| No map integration | Interactive maps showing destinations, routes, hidden gems |
| Intent via keywords | Fine-tuned intent classifier or LLM-based classification |
| No offline mode | PWA with service worker for offline access to saved trips |
| No feedback loop | User ratings on recommendations to improve future suggestions |
