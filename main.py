"""
WanderSoul — FastAPI application entry point.

Destination Discovery & Cultural Experiences platform powered by GenAI.
Serves the API endpoints and the static frontend.

Run with: uvicorn main:app --reload
"""

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import config
from agent.router import handle_request
from data.loader import load_destinations, get_destinations
from models.schemas import TravelRequest, TravelResponse, ErrorResponse

# ─── Logging Setup ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("wandersoul")


# ─── Rate Limiter ────────────────────────────────────────────────

class RateLimiter:
    """Simple in-memory token bucket rate limiter.

    No external dependencies — just tracks request timestamps per IP.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if a request from this IP is allowed.

        Args:
            client_ip: The client's IP address.

        Returns:
            True if allowed, False if rate limited.
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return False

        self._requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter(
    max_requests=config.RATE_LIMIT_REQUESTS,
    window_seconds=config.RATE_LIMIT_WINDOW_SECONDS,
)


# ─── App Lifecycle ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup, cleanup on shutdown."""
    logger.info("Loading destination dataset...")
    load_destinations()
    logger.info("WanderSoul is ready!")
    yield
    logger.info("WanderSoul shutting down.")


# ─── FastAPI App ─────────────────────────────────────────────────

app = FastAPI(
    title="WanderSoul",
    description="Discover destinations and authentic cultural experiences powered by GenAI.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend on any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Exception Handler ───────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions — log details, return generic message.

    Never leaks stack traces or internal error details to the client.
    """
    logger.error("Unhandled exception: %s: %s", type(exc).__name__, str(exc))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Something went wrong. Please try again.",
            detail="Our team has been notified.",
        ).model_dump(),
    )


# ─── API Endpoints ───────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint — confirms the API is running."""
    return {"status": "healthy", "service": "WanderSoul"}


@app.get("/api/destinations")
async def list_destinations():
    """List all destinations in the curated dataset with full details.

    Returns the complete dataset for listing, detail, and filter population.
    """
    destinations = get_destinations()
    return {
        "count": len(destinations),
        "destinations": [
            {
                "id": d["id"],
                "name": d["name"],
                "region": d.get("region") or d.get("state") or "India",
                "category": d.get("category") or "General",
                "description": d.get("description", ""),
                "image_url": d.get("image_url", ""),
                "tags": d.get("tags", []),
                "budget_level": d.get("budget_level", "medium"),
                "best_for_days": d.get("best_for_days", []),
                "accessibility": d.get("accessibility", "moderate"),
            }
            for d in destinations
        ],
    }



@app.post("/api/discover", response_model=TravelResponse)
async def discover(request: TravelRequest, raw_request: Request):
    """Main discovery endpoint — accepts user context, routes through the agent.

    Validates input via Pydantic, rate-limits by IP, then delegates
    to the agent router for intent classification and tool orchestration.

    Args:
        request: Validated TravelRequest body.
        raw_request: Raw FastAPI request (for client IP).

    Returns:
        TravelResponse with results from all invoked tools.
    """
    client_ip = raw_request.client.host if raw_request.client else "unknown"

    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        logger.warning("Rate limit exceeded for %s", client_ip)
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error="Too many requests. Please wait a moment and try again.",
                detail=f"Limit: {config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW_SECONDS}s.",
            ).model_dump(),
        )

    logger.info("Discovery request from %s: query='%s'", client_ip, request.query[:50])

    try:
        response = await handle_request(request)
        return response
    except (TimeoutError, RuntimeError) as exc:
        logger.error("Agent error: %s", str(exc))
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="Our AI is taking longer than expected. Please try again.",
                detail="The language model service may be temporarily slow.",
            ).model_dump(),
        )


# ─── Static Frontend Serving ────────────────────────────────────

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
