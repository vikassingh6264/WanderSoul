"""
Pydantic schemas for request validation and response serialization.

All API data contracts are defined here — FastAPI uses these for
automatic input validation, error messages, and OpenAPI docs.
"""

from pydantic import BaseModel, Field, field_validator


# ─── Request Schemas ─────────────────────────────────────────────

class TravelRequest(BaseModel):
    """User's travel context submitted via the discovery form."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="What the traveler is looking for, in natural language.",
        examples=["I want to explore hidden temples and street food in Rajasthan"],
    )
    budget: str = Field(
        ...,
        description="Budget level for the trip.",
        examples=["budget"],
    )
    days: int = Field(
        ...,
        ge=1,
        le=30,
        description="Number of days available for the trip.",
        examples=[3],
    )
    interests: list[str] = Field(
        default_factory=list,
        description="List of interest tags (e.g. 'street-food', 'heritage').",
        examples=[["street-food", "heritage", "crafts"]],
    )
    accessibility: str = Field(
        default="none",
        description="Mobility/accessibility needs.",
        examples=["wheelchair-friendly"],
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("query must contain at least 3 non-whitespace characters")
        if len(cleaned) > 500:
            raise ValueError("query must be at most 500 characters")
        return cleaned

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"low", "medium", "high"}:
            raise ValueError("budget must be one of: low, medium, high")
        return normalized

    @field_validator("interests", mode="before")
    @classmethod
    def validate_interests(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        cleaned = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    cleaned.append(stripped)
        return cleaned

    @field_validator("accessibility")
    @classmethod
    def validate_accessibility(cls, value: str) -> str:
        if value is None:
            return "none"
        cleaned = value.strip().lower()
        return cleaned or "none"


# ─── Response Schemas ────────────────────────────────────────────

class DestinationResult(BaseModel):
    """A single recommended destination."""

    name: str = Field(..., description="Destination name.")
    region: str = Field(..., description="Region or state.")
    match_reason: str = Field(..., description="Why this destination fits the traveler.")
    budget_tip: str = Field(default="", description="Budget-specific tip.")
    highlights: list[str] = Field(default_factory=list, description="Top highlights.")


class HiddenGemResult(BaseModel):
    """A hidden gem / off-the-beaten-path spot."""

    name: str = Field(..., description="Name of the hidden gem.")
    location: str = Field(..., description="Where to find it.")
    description: str = Field(..., description="Vivid description of the gem.")
    why_hidden: str = Field(default="", description="Why most tourists miss this.")
    local_tip: str = Field(default="", description="Insider tip from locals.")


class StoryResult(BaseModel):
    """An immersive storytelling narrative for a destination."""

    destination: str = Field(..., description="Destination the story is about.")
    narrative: str = Field(..., description="The immersive story text.")
    themes: list[str] = Field(default_factory=list, description="Key cultural themes.")


class HeritageResult(BaseModel):
    """A heritage site or cultural practice worth promoting."""

    name: str = Field(..., description="Heritage site or practice name.")
    significance: str = Field(..., description="Why this heritage matters.")
    how_to_engage: str = Field(..., description="How travelers can engage respectfully.")
    preservation_note: str = Field(default="", description="Current preservation status.")


class EventResult(BaseModel):
    """A local event or festival recommendation."""

    name: str = Field(..., description="Event name.")
    location: str = Field(..., description="Where the event takes place.")
    timing: str = Field(..., description="When the event occurs.")
    description: str = Field(..., description="Contextualized event description.")
    traveler_relevance: str = Field(default="", description="Why this event fits the traveler.")


class ExperienceResult(BaseModel):
    """An authentic cultural experience to connect with."""

    name: str = Field(..., description="Experience name.")
    type: str = Field(..., description="Type: workshop, homestay, tour, etc.")
    description: str = Field(..., description="What the traveler will do/learn.")
    budget_estimate: str = Field(default="", description="Approximate cost.")
    booking_tip: str = Field(default="", description="How to book or find this.")


class TravelResponse(BaseModel):
    """Complete response from the discovery agent."""

    intent: str = Field(..., description="Classified intent of the query.")
    destinations: list[DestinationResult] = Field(default_factory=list)
    hidden_gems: list[HiddenGemResult] = Field(default_factory=list)
    story: StoryResult | None = Field(default=None)
    heritage: list[HeritageResult] = Field(default_factory=list)
    events: list[EventResult] = Field(default_factory=list)
    experiences: list[ExperienceResult] = Field(default_factory=list)
    summary: str = Field(default="", description="Brief summary of all results.")


class ErrorResponse(BaseModel):
    """Generic error response — no stack traces leaked to client."""

    error: str = Field(..., description="User-friendly error message.")
    detail: str = Field(
        default="",
        description="Additional context (never raw exception details).",
    )
